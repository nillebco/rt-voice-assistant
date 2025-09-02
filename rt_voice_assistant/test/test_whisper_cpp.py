import pytest
from unittest.mock import patch, MagicMock, mock_open
from ..bricks.stt.whispercpp import transcribe


class TestWhisperCpp:
    """Test class for whispercpp functionality with mocked dependencies."""

    @pytest.fixture(autouse=True)
    def setup_mocks(self):
        """Setup all necessary mocks for each test."""
        self.os_patcher = patch("rt_voice_assistant.bricks.stt.whispercpp.os")
        self.subprocess_patcher = patch(
            "rt_voice_assistant.bricks.stt.whispercpp.subprocess"
        )
        self.shutil_patcher = patch("rt_voice_assistant.bricks.stt.whispercpp.shutil")
        self.open_patcher = patch("builtins.open", new_callable=mock_open)
        self.uuid_patcher = patch("rt_voice_assistant.bricks.stt.whispercpp.uuid")
        self.detect_paths_patcher = patch(
            "rt_voice_assistant.bricks.stt.whispercpp.detect_paths"
        )

        # Start all patches
        self.mock_os = self.os_patcher.start()
        self.mock_subprocess = self.subprocess_patcher.start()
        self.mock_shutil = self.shutil_patcher.start()
        self.mock_open = self.open_patcher.start()
        self.mock_uuid = self.uuid_patcher.start()
        self.mock_detect_paths = self.detect_paths_patcher.start()

        # Setup common mock returns
        self.mock_os.getenv.side_effect = lambda key, default=None: {
            "WHISPER_CPP_DIR": "./whisper.cpp",
            "WHISPER_BINARY": "./whisper.cpp/build/bin/whisper-cli",
            "WHISPER_CPP_DOCKER_IMAGE": "ghcr.io/ggml-org/whisper.cpp:main",
        }.get(key, default)

        # Mock os.path.expanduser for home directory
        self.mock_os.path.expanduser.return_value = "/test/home"

        self.mock_os.path.isdir.return_value = False
        # Mock path existence for the new detect_paths logic
        self.mock_os.path.exists.side_effect = lambda path: {
            # Whisper binary paths
            "/test/home/whisper.cpp/build/bin/whisper-cli": True,
            "./whisper.cpp/build/bin/whisper-cli": True,
            # Models directory paths
            "./models": True,
            "/test/home/whisper.cpp/models": True,
            "./whisper.cpp/models": True,
            # Model files
            "./models/ggml-small.en.bin": True,
            "./models/ggml-small.fr.bin": True,
            "/test/home/whisper.cpp/models/ggml-small.en.bin": True,
            "/test/home/whisper.cpp/models/ggml-small.fr.bin": True,
            "./whisper.cpp/models/ggml-small.en.bin": True,
            "./whisper.cpp/models/ggml-small.fr.bin": True,
            # Output files
            "outputs/out-test-uuid.txt": True,
            "outputs/out-test-uuid.json": True,
        }.get(path, False)

        # Mock directory checks
        self.mock_os.path.isdir.side_effect = lambda path: {
            "./models": True,
            "/test/home/whisper.cpp/models": True,
            "./whisper.cpp/models": True,
            "outputs": False,
            "audios": False,
        }.get(path, False)

        self.mock_os.path.basename.return_value = "test_audio.wav"
        self.mock_os.path.join.return_value = "audios/test_audio.wav"
        self.mock_os.getcwd.return_value = "/test/working/dir"

        self.mock_uuid.uuid4.return_value = "test-uuid"

        # Setup detect_paths mock returns
        self.mock_detect_paths.return_value = (
            "/test/home/whisper.cpp/build/bin/whisper-cli",
            "./models/ggml-small.en.bin",
        )

        yield

        # Stop all patches
        self.os_patcher.stop()
        self.subprocess_patcher.stop()
        self.shutil_patcher.stop()
        self.open_patcher.stop()
        self.uuid_patcher.stop()
        self.detect_paths_patcher.stop()

    def test_transcribe_with_local_binary(self):
        """Test transcription using local whisper binary."""
        # Setup detect_paths to return local binary path
        self.mock_detect_paths.return_value = (
            "/test/home/whisper.cpp/build/bin/whisper-cli",
            "./models/ggml-small.en.bin",
        )

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"test stdout"
        mock_process.stderr = b"test stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading
        mock_file_content = '{"transcription": [{"text": "Hello world"}]}'
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        # Call function
        result = transcribe("test_audio.wav", model="small", language="en")

        # Log the actual command that was executed
        call_args = self.mock_subprocess.run.call_args[0][0]
        print(f"\nLOCAL BINARY COMMAND: {call_args}")
        expected_command = [
            "/test/home/whisper.cpp/build/bin/whisper-cli",
            "-m",
            "./models/ggml-small.en.bin",
            "-f",
            "test_audio.wav",
            "-ojf",
            "-of",
            "outputs/out-test-uuid",
        ]

        assert call_args == expected_command
        # Assertions
        assert result == "Hello world"
        self.mock_os.mkdir.assert_called()
        self.mock_subprocess.run.assert_called_once()
        self.mock_os.remove.assert_called()

    def test_transcribe_with_docker(self):
        """Test transcription using Docker when local binary not found."""
        # Setup detect_paths to return None for binary (will use Docker)
        self.mock_detect_paths.return_value = (None, "./models/ggml-small.en.bin")

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"docker stdout"
        mock_process.stderr = b"docker stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading
        mock_file_content = '{"transcription": [{"text": "Docker test"}]}'
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        # Call function
        result = transcribe("test_audio.wav", model="small", language="en")

        # Log the actual command that was executed
        call_args = self.mock_subprocess.run.call_args[0][0]
        print(f"\nDOCKER COMMAND: {call_args}")

        expected_command = [
            "docker",
            "run",
            "-it",
            "--rm",
            "-v",
            "/test/working/dir/models:/models",
            "-v",
            "/test/working/dir/audios:/audios",
            "-v",
            "/test/working/dir/outputs:/outputs",
            "ghcr.io/ggml-org/whisper.cpp:main",
            '"whisper-cli -m /models/ggml-small.en.bin -f /audios/test_audio.wav -ojf -of /outputs/out-test-uuid"',
        ]

        assert call_args == expected_command

        # Assertions
        assert result == "Docker test"
        # Note: shutil.copy2 is only called when the Docker path is taken and audio_dest_path != input_wav_path
        # In this test, they are different paths, so copy2 should be called
        self.mock_shutil.copy2.assert_called_once()
        self.mock_subprocess.run.assert_called_once()
        self.mock_os.remove.assert_called()

    def test_transcribe_with_docker_no_copy_needed(self):
        """Test Docker transcription when audio file is already in audios folder."""
        # Setup detect_paths to return None for binary (will use Docker)
        self.mock_detect_paths.return_value = (None, "./models/ggml-small.en.bin")

        # Mock path operations to simulate audio file already in audios folder
        self.mock_os.path.basename.return_value = "test_audio.wav"
        self.mock_os.path.join.return_value = "audios/test_audio.wav"

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"docker no copy stdout"
        mock_process.stderr = b"docker no copy stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading
        mock_file_content = '{"transcription": [{"text": "No copy needed"}]}'
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        # Call function with audio path that's already in audios folder
        result = transcribe("audios/test_audio.wav", model="small", language="en")

        # Log the actual command that was executed
        call_args = self.mock_subprocess.run.call_args[0][0]
        print(f"\nDOCKER NO COPY COMMAND: {call_args}")

        # Assertions
        assert result == "No copy needed"
        # shutil.copy2 should NOT be called since audio_dest_path == input_wav_path
        self.mock_shutil.copy2.assert_not_called()
        self.mock_subprocess.run.assert_called_once()
        self.mock_os.remove.assert_called()

    def test_transcribe_model_not_found(self):
        """Test transcription when model file doesn't exist."""
        # Setup detect_paths to raise an exception
        self.mock_detect_paths.side_effect = ValueError(
            "No valid models directory found"
        )

        # Call function and expect exception
        with pytest.raises(ValueError, match="No valid models directory found"):
            transcribe("test_audio.wav", model="small", language="en")

    def test_transcribe_subprocess_error(self):
        """Test transcription when subprocess fails."""
        # Setup detect_paths to return local binary path
        self.mock_detect_paths.return_value = (
            "/test/home/whisper.cpp/build/bin/whisper-cli",
            "./models/ggml-small.en.bin",
        )

        # Mock subprocess error
        self.mock_subprocess.run.side_effect = self.mock_subprocess.CalledProcessError(
            returncode=1, cmd=["whisper-cli"], stderr=b"Process failed"
        )

        # Call function - it should return None due to exception handling
        result = transcribe("test_audio.wav", model="small", language="en")

        # Assertions - function should return None when subprocess fails
        assert result is None
        self.mock_subprocess.run.assert_called_once()

    def test_transcribe_ffmpeg_error(self):
        """Test transcription when ffmpeg conversion fails."""
        # Setup detect_paths to return local binary path
        self.mock_detect_paths.return_value = (
            "/test/home/whisper.cpp/build/bin/whisper-cli",
            "./models/ggml-small.en.bin",
        )

        # Mock ffmpeg error
        self.mock_subprocess.run.side_effect = self.mock_subprocess.CalledProcessError(
            returncode=1, cmd=["ffmpeg"], stderr=b"FFmpeg failed"
        )

        # Call function - it should return None due to exception handling
        result = transcribe("test_audio.wav", model="small", language="en")

        # Assertions - function should return None when ffmpeg fails
        assert result is None
        self.mock_subprocess.run.assert_called_once()

    def test_transcribe_file_read_error(self):
        """Test transcription when JSON file cannot be read."""
        # Setup detect_paths to return local binary path
        self.mock_detect_paths.return_value = (
            "/test/home/whisper.cpp/build/bin/whisper-cli",
            "./models/ggml-small.en.bin",
        )

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"test stdout"
        mock_process.stderr = b"test stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading error
        self.mock_open.side_effect = Exception("File read error")

        # Call function - it should return None due to exception handling
        result = transcribe("test_audio.wav", model="small", language="en")

        # Assertions - function should return None when file reading fails
        assert result is None
        self.mock_subprocess.run.assert_called_once()

    def test_transcribe_with_custom_whisper_cpp_dir(self):
        """Test transcription with custom whisper.cpp directory."""
        # Setup detect_paths to return custom binary path
        self.mock_detect_paths.return_value = (
            "/custom/path/build/bin/whisper-cli",
            "/custom/path/models/ggml-small.en.bin",
        )

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"custom path stdout"
        mock_process.stderr = b"custom path stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading
        mock_file_content = '{"transcription": [{"text": "Custom path test"}]}'
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        # Call function with custom directory
        result = transcribe(
            "test_audio.wav",
            model="small",
            language="en",
            whisper_cpp_dir="/custom/path",
        )

        # Log the actual command that was executed
        call_args = self.mock_subprocess.run.call_args[0][0]
        print(f"\nCUSTOM PATH COMMAND: {call_args}")

        # Assertions
        assert result == "Custom path test"
        self.mock_subprocess.run.assert_called_once()
        # Verify the custom path is used in the command
        assert "/custom/path/build/bin/whisper-cli" in call_args

    def test_transcribe_with_language_parameter(self):
        """Test transcription with language parameter."""
        # Setup detect_paths to return local binary path with French model
        self.mock_detect_paths.return_value = (
            "/test/home/whisper.cpp/build/bin/whisper-cli",
            "./models/ggml-small.fr.bin",
        )

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"french stdout"
        mock_process.stderr = b"french stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading
        mock_file_content = '{"transcription": [{"text": "Bonjour le monde"}]}'
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        # Call function with French language
        result = transcribe("test_audio.wav", model="small", language="fr")

        # Log the actual command that was executed
        call_args = self.mock_subprocess.run.call_args[0][0]
        print(f"\nLANGUAGE PARAMETER COMMAND: {call_args}")

        # Assertions
        assert result == "Bonjour le monde"
        # Verify the command includes language parameter in the model path
        # The model path should include the language: 'ggml-small.fr.bin'
        # Convert the command list to a string to search for the pattern
        command_str = " ".join(call_args)
        assert ".fr.bin" in command_str
        assert "ggml-small.fr.bin" in command_str

    def test_transcribe_with_elevated_docker(self):
        """Test transcription using Docker with sudo when WHISPER_CPP_USE_ELEVATED_DOCKER is true."""
        # Setup detect_paths to return None for binary (will use Docker)
        self.mock_detect_paths.return_value = (None, "./models/ggml-small.en.bin")

        # Mock environment variable for elevated Docker
        self.mock_os.getenv.side_effect = lambda key, default=None: {
            "WHISPER_CPP_DIR": "./whisper.cpp",
            "WHISPER_BINARY": "./whisper.cpp/build/bin/whisper-cli",
            "WHISPER_CPP_DOCKER_IMAGE": "ghcr.io/ggml-org/whisper.cpp:main",
            "WHISPER_CPP_USE_ELEVATED_DOCKER": "true",
        }.get(key, default)

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"elevated docker stdout"
        mock_process.stderr = b"elevated docker stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading
        mock_file_content = '{"transcription": [{"text": "Elevated Docker test"}]}'
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        # Call function
        result = transcribe("test_audio.wav", model="small", language="en")

        # Log the actual command that was executed
        call_args = self.mock_subprocess.run.call_args[0][0]
        print(f"\nELEVATED DOCKER COMMAND: {call_args}")

        # Verify that sudo is prepended to the command
        assert call_args[0] == "sudo"
        assert call_args[1] == "docker"
        
        # Verify the full command structure
        expected_command = [
            "sudo",
            "docker",
            "run",
            "-it",
            "--rm",
            "-v",
            "/test/working/dir/models:/models",
            "-v",
            "/test/working/dir/audios:/audios",
            "-v",
            "/test/working/dir/outputs:/outputs",
            "ghcr.io/ggml-org/whisper.cpp:main",
            '"whisper-cli -m /models/ggml-small.en.bin -f /audios/test_audio.wav -ojf -of /outputs/out-test-uuid"',
        ]
        
        assert call_args == expected_command

        # Assertions
        assert result == "Elevated Docker test"
        self.mock_shutil.copy2.assert_called_once()
        self.mock_subprocess.run.assert_called_once()
        self.mock_os.remove.assert_called()

    def test_transcribe_with_elevated_docker_false(self):
        """Test transcription using Docker without sudo when WHISPER_CPP_USE_ELEVATED_DOCKER is false."""
        # Setup detect_paths to return None for binary (will use Docker)
        self.mock_detect_paths.return_value = (None, "./models/ggml-small.en.bin")

        # Mock environment variable for non-elevated Docker
        self.mock_os.getenv.side_effect = lambda key, default=None: {
            "WHISPER_CPP_DIR": "./whisper.cpp",
            "WHISPER_BINARY": "./whisper.cpp/build/bin/whisper-cli",
            "WHISPER_CPP_DOCKER_IMAGE": "ghcr.io/ggml-org/whisper.cpp:main",
            "WHISPER_CPP_USE_ELEVATED_DOCKER": "false",
        }.get(key, default)

        # Mock subprocess result
        mock_process = MagicMock()
        mock_process.stdout = b"non-elevated docker stdout"
        mock_process.stderr = b"non-elevated docker stderr"
        mock_process.check_returncode.return_value = None
        self.mock_subprocess.run.return_value = mock_process

        # Mock file reading
        mock_file_content = '{"transcription": [{"text": "Non-elevated Docker test"}]}'
        self.mock_open.return_value.__enter__.return_value.read.return_value = (
            mock_file_content
        )

        # Call function
        result = transcribe("test_audio.wav", model="small", language="en")

        # Log the actual command that was executed
        call_args = self.mock_subprocess.run.call_args[0][0]
        print(f"\nNON-ELEVATED DOCKER COMMAND: {call_args}")

        # Verify that sudo is NOT prepended to the command
        assert call_args[0] == "docker"
        assert "sudo" not in call_args
        
        # Verify the full command structure (without sudo)
        expected_command = [
            "docker",
            "run",
            "-it",
            "--rm",
            "-v",
            "/test/working/dir/models:/models",
            "-v",
            "/test/working/dir/audios:/audios",
            "-v",
            "/test/working/dir/outputs:/outputs",
            "ghcr.io/ggml-org/whisper.cpp:main",
            '"whisper-cli -m /models/ggml-small.en.bin -f /audios/test_audio.wav -ojf -of /outputs/out-test-uuid"',
        ]
        
        assert call_args == expected_command

        # Assertions
        assert result == "Non-elevated Docker test"
        self.mock_shutil.copy2.assert_called_once()
        self.mock_subprocess.run.assert_called_once()
        self.mock_os.remove.assert_called()
