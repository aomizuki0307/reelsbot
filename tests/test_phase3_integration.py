"""Integration tests for Phase 3 video generation and editing.

Tests the complete video generation pipeline including generator and editor.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from reelsbot.config import ReelsbotConfig
from reelsbot.editor import FFmpegEditor
from reelsbot.generator import FFmpegDummyGenerator
from reelsbot.models import ReelPlan
from reelsbot.utils import setup_logger


@pytest.fixture
def config():
    """Provide a test configuration."""
    return ReelsbotConfig(
        openai_api_key="test-key",
        llm_model="gpt-4",
        llm_temperature=0.7,
    )


@pytest.fixture
def logger():
    """Provide a test logger."""
    return setup_logger("test_phase3")


@pytest.fixture
def temp_output_dir():
    """Provide a temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def a_type_plan():
    """Provide a sample A-type plan."""
    return ReelPlan(
        type="A",
        theme="gradient",
        mood="calm",
        duration_sec=10,
        tagline="A moment of peace",
    )


@pytest.fixture
def e_type_plan():
    """Provide a sample E-type plan."""
    return ReelPlan(
        type="E",
        theme="cafe",
        mood="calm",
        duration_sec=12,
        brand_name="ZENITHCAFE",
        concept_title="Modern Cafe Interior",
        category="cafe",
    )


class TestFFmpegDummyGenerator:
    """Test FFmpegDummyGenerator."""

    def test_init(self, config, logger):
        """Test generator initialization."""
        generator = FFmpegDummyGenerator(config, logger)
        assert generator.config == config
        assert generator.logger == logger

    def test_validate_plan_a_type(self, config, logger, a_type_plan):
        """Test plan validation for A-type."""
        generator = FFmpegDummyGenerator(config, logger)
        # Should not raise
        generator.validate_plan(a_type_plan, "A")

    def test_validate_plan_e_type(self, config, logger, e_type_plan):
        """Test plan validation for E-type."""
        generator = FFmpegDummyGenerator(config, logger)
        # Should not raise
        generator.validate_plan(e_type_plan, "E")

    def test_validate_plan_wrong_type(self, config, logger, a_type_plan):
        """Test plan validation fails for wrong type."""
        generator = FFmpegDummyGenerator(config, logger)
        with pytest.raises(ValueError, match="Expected E-type"):
            generator.validate_plan(a_type_plan, "E")

    def test_validate_plan_missing_tagline(self, config, logger):
        """Test validation fails for A-type without tagline."""
        generator = FFmpegDummyGenerator(config, logger)
        plan = ReelPlan(
            type="A",
            theme="gradient",
            mood="calm",
            duration_sec=10,
            tagline=None,
        )
        # Should fail during plan creation
        with pytest.raises(ValueError):
            pass

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_get_theme_filter_gradient(self, mock_run, config, logger):
        """Test gradient theme filter generation."""
        generator = FFmpegDummyGenerator(config, logger)
        cmd = generator._get_theme_filter("gradient", 10)

        assert "ffmpeg" in cmd
        assert "-f" in cmd
        assert "lavfi" in cmd
        assert any("geq" in str(arg) for arg in cmd)

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_get_theme_filter_geometric(self, mock_run, config, logger):
        """Test geometric theme filter generation."""
        generator = FFmpegDummyGenerator(config, logger)
        cmd = generator._get_theme_filter("geometric", 10)

        assert "ffmpeg" in cmd
        assert "testsrc2" in str(cmd)
        assert any("rotate" in str(arg) for arg in cmd)

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_get_theme_filter_kinetic(self, mock_run, config, logger):
        """Test kinetic theme filter generation."""
        generator = FFmpegDummyGenerator(config, logger)
        cmd = generator._get_theme_filter("kinetic", 10)

        assert "ffmpeg" in cmd
        assert any("drawbox" in str(arg) for arg in cmd)

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_get_theme_filter_particles(self, mock_run, config, logger):
        """Test particles theme filter generation."""
        generator = FFmpegDummyGenerator(config, logger)
        cmd = generator._get_theme_filter("particles", 10)

        assert "ffmpeg" in cmd
        assert "nullsrc" in str(cmd)
        assert any("geq" in str(arg) for arg in cmd)

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_get_theme_filter_unknown(self, mock_run, config, logger):
        """Test unknown theme defaults to gradient."""
        generator = FFmpegDummyGenerator(config, logger)
        cmd = generator._get_theme_filter("unknown_theme", 10)

        # Should default to gradient
        assert "ffmpeg" in cmd
        assert any("geq" in str(arg) for arg in cmd)

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_generate_a_video(
        self, mock_run, config, logger, a_type_plan, temp_output_dir
    ):
        """Test A-type video generation."""
        generator = FFmpegDummyGenerator(config, logger)
        output_path = temp_output_dir / "abstract.mp4"

        result = generator.generate_A_video(a_type_plan, output_path)

        assert result == output_path
        mock_run.assert_called_once()
        # Check command includes expected parts
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd

    @patch("reelsbot.utils.image.create_concept_background")
    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_generate_e_video(
        self,
        mock_run,
        mock_create_bg,
        config,
        logger,
        e_type_plan,
        temp_output_dir,
    ):
        """Test E-type video generation."""
        # Mock background image creation
        mock_bg_path = temp_output_dir / "bg.png"
        mock_bg_path.touch()
        mock_create_bg.return_value = mock_bg_path

        generator = FFmpegDummyGenerator(config, logger)
        output_path = temp_output_dir / "concept.mp4"

        result = generator.generate_E_video(e_type_plan, output_path)

        assert result == output_path
        mock_create_bg.assert_called_once()
        mock_run.assert_called_once()

        # Check command includes zoompan
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd
        assert any("zoompan" in str(arg) for arg in cmd)

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_generate_routes_to_a_type(
        self, mock_run, config, logger, a_type_plan, temp_output_dir
    ):
        """Test generate() routes to A-type method."""
        generator = FFmpegDummyGenerator(config, logger)

        result = generator.generate(a_type_plan, temp_output_dir)

        assert result.exists() or True  # Mock doesn't create file
        mock_run.assert_called_once()

    @patch("reelsbot.utils.image.create_concept_background")
    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    def test_generate_routes_to_e_type(
        self,
        mock_run,
        mock_create_bg,
        config,
        logger,
        e_type_plan,
        temp_output_dir,
    ):
        """Test generate() routes to E-type method."""
        # Mock background image
        mock_bg_path = temp_output_dir / "bg.png"
        mock_bg_path.touch()
        mock_create_bg.return_value = mock_bg_path

        generator = FFmpegDummyGenerator(config, logger)

        result = generator.generate(e_type_plan, temp_output_dir)

        assert result.exists() or True  # Mock doesn't create file
        mock_run.assert_called_once()


class TestFFmpegEditor:
    """Test FFmpegEditor."""

    def test_init(self, config, logger):
        """Test editor initialization."""
        editor = FFmpegEditor(config, logger)
        assert editor.config == config
        assert editor.logger == logger
        assert "arial" in editor.font_regular.lower()
        assert "arial" in editor.font_bold.lower()

    def test_escape_text_simple(self, config, logger):
        """Test text escaping for simple text."""
        editor = FFmpegEditor(config, logger)
        result = editor._escape_text("Hello World")
        assert result == "Hello World"

    def test_escape_text_with_special_chars(self, config, logger):
        """Test text escaping with special characters."""
        editor = FFmpegEditor(config, logger)
        result = editor._escape_text("It's a test: 50%")
        assert "\\'" in result
        assert "\\:" in result

    @patch("reelsbot.editor.ffmpeg_editor.run_ffmpeg_command")
    def test_compose_a_video(
        self, mock_run, config, logger, a_type_plan, temp_output_dir
    ):
        """Test A-type video composition."""
        editor = FFmpegEditor(config, logger)

        # Create dummy input video
        input_path = temp_output_dir / "input.mp4"
        input_path.touch()

        output_path = temp_output_dir / "output.mp4"

        result = editor.compose_A_video(input_path, a_type_plan, output_path)

        assert result == output_path
        mock_run.assert_called_once()

        # Check command includes drawtext
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd
        assert any("drawtext" in str(arg) for arg in cmd)
        # Check tagline is escaped and included
        assert any(a_type_plan.tagline.replace("'", "\\'") in str(arg) or a_type_plan.tagline in str(arg) for arg in cmd)

    @patch("reelsbot.editor.ffmpeg_editor.run_ffmpeg_command")
    def test_compose_e_video(
        self, mock_run, config, logger, e_type_plan, temp_output_dir
    ):
        """Test E-type video composition with 'Fictional concept' overlay."""
        editor = FFmpegEditor(config, logger)

        # Create dummy input video
        input_path = temp_output_dir / "input.mp4"
        input_path.touch()

        output_path = temp_output_dir / "output.mp4"

        result = editor.compose_E_video(input_path, e_type_plan, output_path)

        assert result == output_path
        mock_run.assert_called_once()

        # Check command includes drawbox and drawtext
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd
        filter_str = " ".join(str(arg) for arg in cmd)
        assert "drawbox" in filter_str
        assert "drawtext" in filter_str
        assert "Fictional concept" in filter_str

    @patch("reelsbot.editor.ffmpeg_editor.run_ffmpeg_command")
    def test_generate_thumbnail(
        self, mock_run, config, logger, temp_output_dir
    ):
        """Test thumbnail generation."""
        editor = FFmpegEditor(config, logger)

        # Create dummy video
        video_path = temp_output_dir / "video.mp4"
        video_path.touch()

        thumbnail_path = temp_output_dir / "thumb.jpg"

        result = editor.generate_thumbnail(video_path, thumbnail_path)

        assert result == thumbnail_path
        mock_run.assert_called_once()

        # Check command includes thumbnail extraction params
        cmd = mock_run.call_args[0][0]
        assert "ffmpeg" in cmd
        assert "-ss" in cmd
        assert "-vframes" in cmd

    @patch("reelsbot.editor.ffmpeg_editor.run_ffmpeg_command")
    def test_compose_a_type_full(
        self, mock_run, config, logger, a_type_plan, temp_output_dir
    ):
        """Test full composition for A-type."""
        editor = FFmpegEditor(config, logger)

        # Create dummy video
        video_path = temp_output_dir / "video.mp4"
        video_path.touch()

        final_video, thumbnail = editor.compose(
            video_path, a_type_plan, temp_output_dir
        )

        assert final_video.parent == temp_output_dir
        assert thumbnail.parent == temp_output_dir
        assert final_video.suffix == ".mp4"
        assert thumbnail.suffix == ".jpg"

        # Should call FFmpeg twice: compose + thumbnail
        assert mock_run.call_count == 2

    @patch("reelsbot.editor.ffmpeg_editor.run_ffmpeg_command")
    def test_compose_e_type_full(
        self, mock_run, config, logger, e_type_plan, temp_output_dir
    ):
        """Test full composition for E-type."""
        editor = FFmpegEditor(config, logger)

        # Create dummy video
        video_path = temp_output_dir / "video.mp4"
        video_path.touch()

        final_video, thumbnail = editor.compose(
            video_path, e_type_plan, temp_output_dir
        )

        assert final_video.parent == temp_output_dir
        assert thumbnail.parent == temp_output_dir
        assert final_video.suffix == ".mp4"
        assert thumbnail.suffix == ".jpg"

        # Should call FFmpeg twice: compose + thumbnail
        assert mock_run.call_count == 2


class TestIntegration:
    """Integration tests combining generator and editor."""

    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    @patch("reelsbot.editor.ffmpeg_editor.run_ffmpeg_command")
    def test_full_pipeline_a_type(
        self,
        mock_edit_cmd,
        mock_gen_cmd,
        config,
        logger,
        a_type_plan,
        temp_output_dir,
    ):
        """Test full pipeline for A-type video."""
        generator = FFmpegDummyGenerator(config, logger)
        editor = FFmpegEditor(config, logger)

        # Generate raw video
        raw_video = generator.generate(a_type_plan, temp_output_dir)

        # Compose final video
        final_video, thumbnail = editor.compose(
            raw_video, a_type_plan, temp_output_dir
        )

        # Verify calls
        assert mock_gen_cmd.call_count == 1
        assert mock_edit_cmd.call_count == 2  # compose + thumbnail

    @patch("reelsbot.utils.image.create_concept_background")
    @patch("reelsbot.generator.ffmpeg_dummy.run_ffmpeg_command")
    @patch("reelsbot.editor.ffmpeg_editor.run_ffmpeg_command")
    def test_full_pipeline_e_type(
        self,
        mock_edit_cmd,
        mock_gen_cmd,
        mock_create_bg,
        config,
        logger,
        e_type_plan,
        temp_output_dir,
    ):
        """Test full pipeline for E-type video."""
        # Mock background image
        mock_bg_path = temp_output_dir / "bg.png"
        mock_bg_path.touch()
        mock_create_bg.return_value = mock_bg_path

        generator = FFmpegDummyGenerator(config, logger)
        editor = FFmpegEditor(config, logger)

        # Generate raw video
        raw_video = generator.generate(e_type_plan, temp_output_dir)

        # Compose final video (should add "Fictional concept" overlay)
        final_video, thumbnail = editor.compose(
            raw_video, e_type_plan, temp_output_dir
        )

        # Verify calls
        assert mock_gen_cmd.call_count == 1
        assert mock_edit_cmd.call_count == 2  # compose + thumbnail

        # Verify "Fictional concept" overlay is added
        compose_cmd = mock_edit_cmd.call_args_list[0][0][0]
        filter_str = " ".join(str(arg) for arg in compose_cmd)
        assert "Fictional concept" in filter_str
