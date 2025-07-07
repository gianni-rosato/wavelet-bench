import os
import re
import math
import time
import subprocess
from subprocess import Popen


class CoreVideo:
    """
    Source video class.
    """

    path: str
    name: str
    size: int

    video_width: int
    video_height: int

    def __init__(self, pth: str) -> None:
        self.path = pth
        self.name = os.path.basename(pth)
        self.size = self.get_input_filesize()
        self.video_width, self.video_height = self.get_video_dimensions()

    def get_input_filesize(self) -> int:
        """
        Get the input file size of the distorted video.
        """
        return os.path.getsize(self.path)

    def get_video_dimensions(self) -> tuple[int, int]:
        """
        Get the width & height of the distorted video.
        """
        cmd: list[str] = [
            "ffprobe",
            "-v",
            "error",
            "-select_streams",
            "v:0",
            "-show_entries",
            "stream=width,height",
            "-of",
            "csv=s=x:p=0",
            self.path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(f"Error getting video dimensions: {result.stderr}")

        dimensions: list[str] = result.stdout.strip().split("x")
        return (int(dimensions[0]), int(dimensions[1]))


class DstVideo(CoreVideo):
    """
    Distorted video class containing metric scores.
    """

    # Encoded path
    # We keep this because the encoded video isn't always decodable with FFmpeg
    enc_path: str

    # XPSNR scores
    xpsnr_y: float
    xpsnr_u: float
    xpsnr_v: float
    w_xpsnr: float

    # PSNR
    psnr: float

    # SSIM
    ssim: float

    def __init__(self, pth: str, e_pth: str) -> None:
        self.path = pth
        self.enc_path = e_pth
        self.name = os.path.basename(pth)
        self.size = self.get_input_filesize()
        self.video_width, self.video_height = self.get_video_dimensions()
        self.xpsnr_y = 0.0
        self.xpsnr_u = 0.0
        self.xpsnr_v = 0.0
        self.w_xpsnr = 0.0
        self.psnr = 0.0
        self.ssim = 0.0

    def get_input_filesize(self) -> int:
        """
        Get the input file size of the distorted video.
        """
        return os.path.getsize(self.enc_path)

    def calculate_psnr_ssim(self, src: CoreVideo) -> None:
        """
        Calculate PSNR & SSIM scores between a source video & a distorted video using FFmpeg.
        """
        # Construct FFmpeg command
        cmd: list[str] = [
            "ffmpeg",
            "-i",
            src.path,
            "-i",
            self.path,
            "-filter_complex",
            "[0:v][1:v]psnr=shortest=1;[0:v][1:v]ssim=shortest=1",
            "-f",
            "null",
            "-",
        ]

        process: Popen[str] = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        _, stderr = process.communicate()

        psnr_match = re.search(r"average:(\d+\.\d+)", stderr)
        self.psnr = float(psnr_match.group(1)) if psnr_match else 0

        ssim_match = re.search(r"All:(\d+\.\d+)", stderr)
        self.ssim = float(ssim_match.group(1)) if ssim_match else 0

    def calculate_xpsnr(self, src: CoreVideo) -> None:
        """
        Calculate XPSNR scores between a source video & a distorted video using FFmpeg.
        """

        cmd: list[str] = [
            "ffmpeg",
            "-i",
            self.path,
            "-i",
            src.path,
            "-hide_banner",
            "-lavfi",
            "xpsnr=shortest=1",
            "-f",
            "null",
            "-",
        ]

        process: Popen[str] = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True
        )

        _, stderr = process.communicate()

        # Parse XPSNR scores using regex
        rgx: str = r"XPSNR\s+y:\s*(\d+\.\d+)\s+u:\s*(\d+\.\d+)\s+v:\s*(\d+\.\d+)"
        match = re.search(rgx, stderr)
        if match:
            self.xpsnr_y = float(match.group(1))
            self.xpsnr_u = float(match.group(2))
            self.xpsnr_v = float(match.group(3))
        else:
            self.xpsnr_y = 0.0
            self.xpsnr_u = 0.0
            self.xpsnr_v = 0.0

        maxval: int = 255
        xpsnr_mse_y: float = psnr_to_mse(self.xpsnr_y, maxval)
        xpsnr_mse_u: float = psnr_to_mse(self.xpsnr_u, maxval)
        xpsnr_mse_v: float = psnr_to_mse(self.xpsnr_v, maxval)
        w_xpsnr_mse: float = ((4.0 * xpsnr_mse_y) + xpsnr_mse_u + xpsnr_mse_v) / 6.0
        self.w_xpsnr = 10.0 * math.log10((maxval**2) / w_xpsnr_mse)

    def print_xpsnr(self) -> None:
        """
        Print XPSNR scores.
        """
        print("\033[91mXPSNR\033[0m scores:")
        print(f" XPSNR Y:       \033[1m{self.xpsnr_y:.5f}\033[0m")
        print(f" XPSNR U:       \033[1m{self.xpsnr_u:.5f}\033[0m")
        print(f" XPSNR V:       \033[1m{self.xpsnr_v:.5f}\033[0m")
        print(f" W-XPSNR:       \033[1m{self.w_xpsnr:.5f}\033[0m")

    def print_psnr_ssim(self) -> None:
        """
        Print PSNR & SSIM scores.
        """
        print("PSNR/SSIM scores:")
        print(f" PSNR:          \033[1m{self.psnr:.5f}\033[0m")
        print(f" SSIM:           \033[1m{self.ssim:.5f}\033[0m")


class VideoEnc:
    """
    Video encoding class, containing encoder commands.
    """

    src: CoreVideo
    dst_pth: str
    q: int
    encoder: str
    encoder_args: list[str]
    time: float

    def __init__(
        self,
        src: CoreVideo,
        q: int,
        encoder: str,
        encoder_args: list[str],
        dst_pth: str = "",
    ) -> None:
        self.src = src
        self.q = q
        self.encoder = encoder
        self.encoder_args = encoder_args if encoder_args else [""]

        if not dst_pth:
            base_name = os.path.splitext(src.name)[0]
            ext = self.get_ext()
            self.dst_pth = f"{base_name}_{encoder}_q{q}.{ext}"
        else:
            self.dst_pth = dst_pth

    def get_ext(self) -> str:
        """
        Determine appropriate file extension based on encoder
        """
        if self.encoder == "dirac":
            return "mkv"
        elif self.encoder == "snow":
            return "avi"
        elif self.encoder == "x264":
            return "264"
        else:
            return "dsv"

    def encode(self) -> DstVideo:
        """
        Encode the video using FFmpeg piped to your chosen encoder.
        """

        ff_cmd: list[str] = []
        enc_cmd: list[str] = []
        dec_pth: str = ""

        if self.encoder == "x264":
            enc_cmd = [
                "x264",
                "--demuxer",
                "y4m",
                "--crf",
                f"{self.q}",
                "-o",
                f"{self.dst_pth}",
                "-",
            ]
            dec_pth = self.dst_pth
            if self.encoder_args != [""]:
                enc_cmd.extend(self.encoder_args)
        elif self.encoder == "dsv2":
            enc_cmd = [
                "dsv2",
                "e",
                "-inp=-",
                f"-out={self.dst_pth}",
                f"-qp={self.q}",
                "-y",
            ]
            if self.encoder_args != [""]:
                enc_cmd.extend(self.encoder_args)
            dec_y4m_path = f"{os.path.splitext(self.dst_pth)[0]}_decoded.y4m"
            dec_pth = dec_y4m_path

        if self.encoder not in ["snow"]:
            ff_cmd = [
                "ffmpeg",
                "-hide_banner",
                "-y",
                "-loglevel",
                "error",
                "-i",
                f"{self.src.path}",
                "-pix_fmt",
                "yuv420p",
                "-strict",
                "-2",
                "-f",
                "yuv4mpegpipe",
                "-",
            ]
        else:
            ff_cmd = [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                f"{self.src.path}",
                "-pix_fmt",
                "yuv420p",
                "-c:v",
                "snow",
                "-q:v",
                f"{self.q}",
                f"{self.dst_pth}",
            ]
            if self.encoder_args != [""]:
                ff_cmd.extend(self.encoder_args)

        print(f"Encoding video at Q{self.q} with {self.encoder} ...")
        if self.encoder == "dsv2":
            dec_y4m_path = f"{os.path.splitext(self.dst_pth)[0]}_decoded.y4m"
            ff_proc: Popen[str] = subprocess.Popen(
                ff_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            start_time: float = time.time()
            enc_proc: Popen[str] = subprocess.Popen(
                enc_cmd,
                stdin=ff_proc.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            _, enc_stderr = enc_proc.communicate()
            dec_cmd = [
                "dsv2",
                "d",
                f"-inp={self.dst_pth}",
                f"-out={dec_y4m_path}",
                "-y4m=1",
                "-y",
            ]
            dec_proc: Popen[str] = subprocess.Popen(
                dec_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            _, dec_stderr = dec_proc.communicate()
            encode_time: float = time.time() - start_time
            self.time = encode_time
            print(enc_stderr)
            print(dec_stderr)
            dec_pth = dec_y4m_path
        elif self.encoder != "snow":
            ff_proc: Popen[str] = subprocess.Popen(
                ff_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            start_time: float = time.time()
            enc_proc: Popen[str] = subprocess.Popen(
                enc_cmd,
                stdin=ff_proc.stdout,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            _, stderr = enc_proc.communicate()
            encode_time: float = time.time() - start_time
            self.time = encode_time
            print(stderr)
        else:
            start_time: float = time.time()
            process: Popen[str] = subprocess.Popen(
                ff_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
            )
            _, stderr = process.communicate()
            encode_time: float = time.time() - start_time
            self.time = encode_time
            print(stderr)
            dec_pth = self.dst_pth

        return DstVideo(dec_pth, self.dst_pth)

    def remove_output(self) -> None:
        """
        Remove the output file.
        """
        os.remove(self.dst_pth)
        if self.encoder == "dsv2":
            dec_y4m_path = f"{os.path.splitext(self.dst_pth)[0]}_decoded.y4m"
            if os.path.exists(dec_y4m_path):
                os.remove(dec_y4m_path)


def psnr_to_mse(p: float, m: int) -> float:
    """
    Convert PSNR to MSE (Mean Squared Error). Used in weighted XPSNR calculation.
    """
    return (m**2) / (10 ** (p / 10))
