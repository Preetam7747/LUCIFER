import io
import base64

try:
    import qrcode
except ImportError:
    qrcode = None


def generate_qr(data):
    if qrcode is None:
        raise RuntimeError(
            "QR code support requires the 'qrcode' package."
        )

    qr = qrcode.QRCode(
        version=1,
        box_size=10,
        border=4
    )

    qr.add_data(data)
    qr.make(fit=True)

    image = qr.make_image()

    buffer = io.BytesIO()
    image.save(buffer, format="PNG")

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return encoded


def generate_student_qr(student_id, name):
    data = (
        f"Smart Hostel Management System\n"
        f"Student ID: {student_id}\n"
        f"Name: {name}"
    )

    return generate_qr(data)


def generate_room_qr(room_number, block_name):
    data = (
        f"Smart Hostel Management System\n"
        f"Room: {room_number}\n"
        f"Block: {block_name}"
    )

    return generate_qr(data)