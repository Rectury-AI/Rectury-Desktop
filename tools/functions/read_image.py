import base64
import mimetypes
import struct

from core.workspace import resolve_workspace_path


MAX_IMAGE_BYTES = 4 * 1024 * 1024


def png_size(data):
    if len(data) >= 24 and data[:8] == b"\x89PNG\r\n\x1a\n":
        width, height = struct.unpack(">II", data[16:24])
        return width, height

    return None


def jpeg_size(data):
    if len(data) < 4 or data[:2] != b"\xff\xd8":
        return None

    index = 2

    while index + 9 < len(data):
        if data[index] != 0xFF:
            index += 1
            continue

        marker = data[index + 1]
        index += 2

        if marker in {0xD8, 0xD9}:
            continue

        if index + 2 > len(data):
            return None

        length = struct.unpack(">H", data[index:index + 2])[0]

        if length < 2 or index + length > len(data):
            return None

        if marker in {
            0xC0,
            0xC1,
            0xC2,
            0xC3,
            0xC5,
            0xC6,
            0xC7,
            0xC9,
            0xCA,
            0xCB,
            0xCD,
            0xCE,
            0xCF,
        }:
            height, width = struct.unpack(">HH", data[index + 3:index + 7])
            return width, height

        index += length

    return None


def gif_size(data):
    if len(data) >= 10 and data[:6] in {b"GIF87a", b"GIF89a"}:
        width, height = struct.unpack("<HH", data[6:10])
        return width, height

    return None


def webp_size(data):
    if len(data) >= 30 and data[:4] == b"RIFF" and data[8:12] == b"WEBP":
        if data[12:16] == b"VP8X" and len(data) >= 30:
            width = 1 + int.from_bytes(data[24:27], "little")
            height = 1 + int.from_bytes(data[27:30], "little")
            return width, height

    return None


def image_size(data):
    for detector in (png_size, jpeg_size, gif_size, webp_size):
        size = detector(data)

        if size:
            return size

    return None


def read_image(file_path, state, include_data=True):
    try:
        path = resolve_workspace_path(state.workspace, file_path)
    except ValueError as error:
        return {"error": str(error)}

    if not path.exists() or not path.is_file():
        return {"error": f"image does not exist: {path}"}

    try:
        data = path.read_bytes()
    except OSError as error:
        return {"error": str(error)}

    mime_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"

    if not mime_type.startswith("image/"):
        return {
            "error": f"file is not a recognized image: {path}",
            "code": "not_image",
        }

    width = height = None
    size = image_size(data)

    if size:
        width, height = size

    result = {
        "success": True,
        "file_path": str(path),
        "mime_type": mime_type,
        "bytes": len(data),
        "width": width,
        "height": height,
        "data_included": False,
    }

    if include_data and len(data) <= MAX_IMAGE_BYTES:
        encoded = base64.b64encode(data).decode("ascii")
        result["data_url"] = f"data:{mime_type};base64,{encoded}"
        result["data_included"] = True
    elif include_data:
        result["data_omitted_reason"] = (
            f"image is larger than {MAX_IMAGE_BYTES} bytes"
        )

    return result
