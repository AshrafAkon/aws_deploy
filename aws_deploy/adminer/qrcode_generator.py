import base64

import qrcode

from aws_deploy.cloudformation.parameter.ssm_stored import GeneratedSecret
from aws_deploy.cloudformation.template import CloudformationTemplate
from aws_deploy.config import Config


class OtpQrCodeGenerator:

    def base32secret(self):
        """Return base32 encoded otp secret
-
        Fetches base64 encoded otp secret string.
        Coverts it to base32 and returns converted
        base32 in ascii string format

        Returns:
            str: base32 encoded otp secret
        """
        template = CloudformationTemplate.from_short_name('adminer')
        param = GeneratedSecret(
            template)
        ssm_param_name = param.ssm_param_name('OtpSecretStore')
        ssm_param = param.ssm_stored.get_parameter(ssm_param_name)
        # 'P2kib4vBUpZf5A=='
        base64_bytes: str = ssm_param['Value']  # type: ignore
        secret_bytes = base64.b64decode(base64_bytes, validate=True)
        base32_bytes = base64.b32encode(secret_bytes)
        return base32_bytes.decode('ascii')

    def qr_data(self, otp_secret: str) -> str:
        return f"otpauth://totp/Adminer:{Config().ENV}?secret={otp_secret}&issuer=Adminer"  # noqa: E501

    def generate(self):
        otp_secret = self.base32secret()
        qr_data = self.qr_data(otp_secret)
        # Creating an instance of qrcode
        qr = qrcode.QRCode(
            version=1,
            box_size=10,
            border=5)
        qr.add_data(qr_data)
        qr.make(fit=True)
        img = qr.make_image(fill='black', back_color='white')
        img.save('otp_qrcode.png')
