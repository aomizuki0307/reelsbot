"""Main orchestration layer for the reelsbot pipeline.

This module coordinates all components of the reelsbot system, managing the complete
workflow from plan generation through video creation to publication and storage.
"""

import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Literal

from reelsbot.caption_generator import CaptionGenerator
from reelsbot.config import ReelsbotConfig
from reelsbot.editor import FFmpegEditor
from reelsbot.generator import FFmpegDummyGenerator
from reelsbot.llm_client import LLMClient, create_llm_client
from reelsbot.models import ReelMetadata, ReelPlan
from reelsbot.planner import Planner
from reelsbot.policy_gate import PolicyGate, PolicyViolationError
from reelsbot.publisher import DryRunPublisher
from reelsbot.storage import RunStorage
from reelsbot.utils import ensure_output_dir, setup_logger


class OrchestratorError(Exception):
    """Base exception for orchestrator errors."""
    pass


class Orchestrator:
    """Main workflow coordinator for the reelsbot pipeline.

    The Orchestrator manages the complete pipeline from content planning through
    video generation, editing, captioning, and publishing. It coordinates all
    components and handles error recovery and retry logic.

    Attributes:
        config: System configuration.
        logger: Logger instance for this orchestrator.
        planner: Content planning component.
        policy_gate: Policy validation component.
        generator: Video generation component.
        editor: Video editing/overlay component.
        caption_generator: Caption generation component.
        storage: Metadata storage component.
        publisher: Publishing component (DryRun or Instagram API).

    Example:
        >>> config = load_config()
        >>> logger = setup_logger("run_123")
        >>> orchestrator = Orchestrator(config, logger)
        >>> metadata_list = await orchestrator.run_pipeline(count=1, type_filter="A")
    """

    def __init__(self, config: ReelsbotConfig, logger: logging.Logger):
        """Initialize orchestrator with all required components.

        Args:
            config: System configuration.
            logger: Logger instance for tracking execution.
        """
        self.config = config
        self.logger = logger

        # Create LLM client
        self.llm_client: LLMClient = create_llm_client(config)

        # Initialize all components
        self.planner = Planner(config=config, llm_client=self.llm_client, logger=logger)
        self.policy_gate = PolicyGate(config=config, llm_client=self.llm_client, logger=logger)
        self.generator = FFmpegDummyGenerator(config=config, logger=logger)
        self.editor = FFmpegEditor(config=config, logger=logger)
        self.caption_generator = CaptionGenerator(config=config, llm_client=self.llm_client, logger=logger)
        self.storage = RunStorage(config=config, logger=logger)
        self.publisher = DryRunPublisher(config=config, logger=logger)

        self.logger.info("Orchestrator initialized with all components")

    async def run_pipeline(
        self,
        count: int,
        type_filter: Literal["A", "E"] | None = None,
        mix: bool = False,
        dry_run: bool = True,
    ) -> list[ReelMetadata]:
        """Execute the complete content generation pipeline.

        Main workflow:
        1. Generate run_id and setup output directory
        2. Generate content plans based on filters
        3. For each plan:
           a. Validate with policy gate (retry if needed)
           b. Generate raw video
           c. Edit video with overlays
           d. Generate caption
           e. Create metadata
           f. Publish (dry-run or live)
           g. Save to storage
        4. Return list of generated metadata

        Args:
            count: Number of videos to generate.
            type_filter: Filter by type ("A" or "E"), mutually exclusive with mix.
            mix: Use A/E ratio from config, mutually exclusive with type_filter.
            dry_run: If True, use DryRunPublisher (default). If False, use Instagram API.

        Returns:
            List of ReelMetadata for successfully generated videos.

        Raises:
            OrchestratorError: If pipeline execution fails critically.
            ValueError: If both type_filter and mix are specified.

        Example:
            >>> # Generate 1 A-type video
            >>> metadata = await orchestrator.run_pipeline(count=1, type_filter="A")
            >>>
            >>> # Generate 7 videos with mix ratio
            >>> metadata = await orchestrator.run_pipeline(count=7, mix=True)
        """
        # Validate arguments
        if type_filter and mix:
            raise ValueError("Cannot specify both type_filter and mix")

        # Generate run ID
        run_id = self._generate_run_id()
        self.logger.info(f"Starting pipeline run: {run_id}")
        self.logger.info(f"Parameters: count={count}, type_filter={type_filter}, mix={mix}, dry_run={dry_run}")

        # Create output directory
        output_dir = ensure_output_dir(run_id, self.config.outputs_dir)
        self.logger.info(f"Output directory: {output_dir}")

        # Generate plans
        plans = await self._generate_plans(count, type_filter, mix)
        self.logger.info(f"Generated {len(plans)} content plans")

        # Process each plan
        metadata_list: list[ReelMetadata] = []
        failures: list[dict] = []

        for idx, plan in enumerate(plans, 1):
            self.logger.info(f"Processing plan {idx}/{len(plans)}: {plan.type}-type")

            try:
                metadata = await self._process_single_plan(
                    plan=plan,
                    run_id=run_id,
                    output_dir=output_dir,
                    plan_number=idx,
                )
                metadata_list.append(metadata)
                self.logger.info(f"Successfully processed plan {idx}/{len(plans)}")

            except Exception as e:
                self.logger.error(f"Failed to process plan {idx}/{len(plans)}: {e}", exc_info=True)
                failures.append({
                    "plan_number": idx,
                    "plan_type": plan.type,
                    "error": str(e),
                })
                continue

        # Log summary
        self.logger.info(f"Pipeline complete: {len(metadata_list)} successful, {len(failures)} failed")
        if failures:
            self.logger.warning(f"Failed plans: {failures}")

        return metadata_list

    async def _generate_plans(
        self,
        count: int,
        type_filter: Literal["A", "E"] | None,
        mix: bool,
    ) -> list[ReelPlan]:
        """Generate content plans based on parameters.

        Args:
            count: Number of plans to generate.
            type_filter: Type filter ("A" or "E").
            mix: Whether to use mixed A/E ratio.

        Returns:
            List of ReelPlan objects.
        """
        if type_filter:
            # Generate specific type
            self.logger.info(f"Generating {count} {type_filter}-type plans")
            plans = [await self._create_single_plan(type_filter) for _ in range(count)]
        elif mix:
            # Generate mixed ratio
            self.logger.info(f"Generating {count} plans with A/E ratio {self.config.default_a_ratio}:{self.config.default_e_ratio}")
            plans = await self.planner.generate_daily_plan(count=count)
        else:
            # Default to A-type if no filter specified
            self.logger.info(f"No type specified, defaulting to {count} A-type plans")
            plans = [await self._create_single_plan("A") for _ in range(count)]

        return plans

    async def _create_single_plan(self, plan_type: Literal["A", "E"]) -> ReelPlan:
        """Create a single plan for testing purposes.

        Uses the planner to generate a single plan of the specified type.

        Args:
            plan_type: Type of plan to create ("A" or "E").

        Returns:
            Generated ReelPlan.
        """
        self.logger.debug(f"Creating single {plan_type}-type plan")

        # Use planner to generate a single plan
        if plan_type == "A":
            plan = await self.planner.generate_abstract_plan()
        else:
            plan = await self.planner.generate_educational_plan()

        return plan

    async def _process_single_plan(
        self,
        plan: ReelPlan,
        run_id: str,
        output_dir: Path,
        plan_number: int,
    ) -> ReelMetadata:
        """Process a single plan through the complete pipeline.

        Args:
            plan: Content plan to process.
            run_id: Unique run identifier.
            output_dir: Output directory for this run.
            plan_number: Sequential number of this plan in the batch.

        Returns:
            ReelMetadata for the generated video.

        Raises:
            Exception: If any pipeline step fails.
        """
        # Step 1: Validate with policy gate (with retry)
        self.logger.info(f"Step 1/7: Validating plan with policy gate")
        validated_plan = await self._validate_with_retry(plan)
        self.logger.info(f"Policy validation passed")

        # Step 2: Generate raw video
        self.logger.info(f"Step 2/7: Generating raw video")
        raw_video_path = output_dir / f"raw_video_{plan_number}.mp4"
        raw_video_path = self.generator.generate(validated_plan, output_dir)
        self.logger.info(f"Raw video generated: {raw_video_path}")

        # Step 3: Edit video with overlays
        self.logger.info(f"Step 3/7: Editing video with overlays")
        final_video_path = output_dir / f"video_{plan_number}.mp4"
        final_video_path = await self.editor.edit_video(
            plan=validated_plan,
            input_path=raw_video_path,
            output_path=final_video_path,
        )
        self.logger.info(f"Video edited: {final_video_path}")

        # Step 4: Generate thumbnail
        self.logger.info(f"Step 4/7: Generating thumbnail")
        thumbnail_path = output_dir / f"thumbnail_{plan_number}.jpg"
        thumbnail_path = await self.editor.create_thumbnail(
            video_path=final_video_path,
            output_path=thumbnail_path,
            timestamp=1.0,
        )
        self.logger.info(f"Thumbnail created: {thumbnail_path}")

        # Step 5: Generate caption
        self.logger.info(f"Step 5/7: Generating caption")
        caption_data = await self.caption_generator.generate_caption(validated_plan)
        self.logger.info(f"Caption generated: {caption_data['caption'][:50]}...")

        # Step 6: Create metadata
        self.logger.info(f"Step 6/7: Creating metadata")
        metadata = ReelMetadata(
            run_id=run_id,
            timestamp=datetime.now(),
            plan=validated_plan,
            caption=caption_data["caption"],
            hashtags=caption_data["hashtags"],
            video_path=final_video_path,
            thumbnail_path=thumbnail_path,
            status="generated",
        )

        # Step 7: Publish and save
        self.logger.info(f"Step 7/7: Publishing and saving metadata")

        # Publish (dry-run or live)
        publish_result = await self.publisher.publish(metadata)
        self.logger.info(f"Published (DRY_RUN): {publish_result}")

        # Save metadata to storage
        metadata_path = await self.storage.save_metadata(metadata)
        self.logger.info(f"Metadata saved: {metadata_path}")

        return metadata

    async def _validate_with_retry(self, plan: ReelPlan) -> ReelPlan:
        """Validate plan with policy gate, with retry on failure.

        If validation fails, regenerate the plan and retry up to POLICY_MAX_RETRY times.

        Args:
            plan: Plan to validate.

        Returns:
            Validated plan (may be regenerated).

        Raises:
            PolicyViolationError: If all retry attempts are exhausted.
        """
        max_retries = self.config.policy_max_retry
        current_plan = plan

        for attempt in range(1, max_retries + 1):
            try:
                self.logger.debug(f"Policy validation attempt {attempt}/{max_retries}")

                # Validate the plan
                validation_result = await self.policy_gate.validate(current_plan)

                if validation_result["is_valid"]:
                    self.logger.info(f"Policy validation passed on attempt {attempt}")
                    return current_plan
                else:
                    # Validation failed
                    violations = validation_result.get("violations", [])
                    self.logger.warning(f"Policy validation failed on attempt {attempt}: {violations}")

                    if attempt < max_retries:
                        # Regenerate plan for next attempt
                        self.logger.info(f"Regenerating plan for retry {attempt + 1}")
                        current_plan = await self._create_single_plan(plan.type)
                    else:
                        # Max retries exhausted
                        raise PolicyViolationError(
                            f"Policy validation failed after {max_retries} attempts. "
                            f"Last violations: {violations}"
                        )

            except PolicyViolationError:
                # Re-raise policy violations
                raise
            except Exception as e:
                self.logger.error(f"Error during policy validation attempt {attempt}: {e}")
                if attempt >= max_retries:
                    raise PolicyViolationError(
                        f"Policy validation failed after {max_retries} attempts due to error: {e}"
                    )
                # Regenerate and retry
                current_plan = await self._create_single_plan(plan.type)

        # Should not reach here, but raise error just in case
        raise PolicyViolationError(f"Policy validation failed after {max_retries} attempts")

    def _generate_run_id(self) -> str:
        """Generate unique run ID.

        Format: run_YYYYMMDD_HHMMSS

        Returns:
            Unique run identifier string.

        Example:
            >>> orchestrator._generate_run_id()
            'run_20251220_123456'
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"run_{timestamp}"
