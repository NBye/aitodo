import types

import hashlib,hmac,json,time,httpx
from datetime import datetime
from src.utils.errors import CodeError

import config

def sign(key, msg):
    return hmac.new(key, msg.encode("utf-8"), hashlib.sha256).digest()

class Sms():
    def __init__(self, SecretId=None, SecretKey=None, EndPoint=None, Region=None, SdkAppId=None,SignName=None):
        self.SecretId                   = SecretId          or config.TENCENT_SECRETID
        self.SecretKey                  = SecretKey         or config.TENCENT_SECRETKEY
        self.EndPoint                   = EndPoint          or config.TENCENT_SMS_ENDPOINT
        self.Region                     = Region            or config.TENCENT_SMS_REGION
        self.SdkAppId                   = SdkAppId          or config.TENCENT_SMS_SDKAPPID
        self.SignName                   = SignName          or config.TENCENT_SMS_SIGNNAME
        if not self.SecretKey:
            raise CodeError('未配置腾讯云SDK参数')


    async def send(self,phone, template_id, params=[]):
        service,action                  = "sms","SendSms"
        algorithm,version               = "TC3-HMAC-SHA256","2021-01-11"
        payload = json.dumps({
            "PhoneNumberSet"            : [ str(phone) ],
            "SmsSdkAppId"               : self.SdkAppId,
            "SignName"                  : self.SignName,
            "TemplateId"                : template_id,
            "TemplateParamSet"          : params
        })
        timestamp                       = int(time.time())
        date                            = datetime.utcfromtimestamp(timestamp).strftime("%Y-%m-%d")

        # ************* 步骤 1：拼接规范请求串 *************
        http_request_method             = "POST"
        canonical_uri                   = "/"
        canonical_querystring           = ""
        ct                              = "application/json; charset=utf-8"
        canonical_headers               = "content-type:%s\nhost:%s\nx-tc-action:%s\n" % (ct, self.EndPoint, action.lower())
        signed_headers                  = "content-type;host;x-tc-action"
        hashed_request_payload          = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        canonical_request               = (http_request_method + "\n" +
                                        canonical_uri + "\n" +
                                        canonical_querystring + "\n" +
                                        canonical_headers + "\n" +
                                        signed_headers + "\n" +
                                        hashed_request_payload)
        # ************* 步骤 2：拼接待签名字符串 *************
        credential_scope                = date + "/" + service + "/" + "tc3_request"
        hashed_canonical_request        = hashlib.sha256(canonical_request.encode("utf-8")).hexdigest()
        string_to_sign                  = (algorithm + "\n" +
                                        str(timestamp) + "\n" +
                                        credential_scope + "\n" +
                                        hashed_canonical_request)

        # ************* 步骤 3：计算签名 *************
        secret_date                     = sign(("TC3" + self.SecretKey).encode("utf-8"), date)
        secret_service                  = sign(secret_date, service)
        secret_signing                  = sign(secret_service, "tc3_request")
        signature                       = hmac.new(secret_signing, string_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()

        # ************* 步骤 4：拼接 Authorization *************
        authorization                   = (algorithm + " " +
                                        "Credential=" + self.SecretId + "/" + credential_scope + ", " +
                                        "SignedHeaders=" + signed_headers + ", " +
                                        "Signature=" + signature)

        # ************* 步骤 5：构造并发起请求 *************
        headers                         = {
            "Authorization"             : authorization,
            "Content-Type"              : "application/json; charset=utf-8",
            "Host"                      : self.EndPoint,
            "X-TC-Action"               : action,
            "X-TC-Timestamp"            : str(timestamp),
            "X-TC-Version"              : version
        }
        if self.Region:
            headers["X-TC-Region"]      = self.Region
        data                            = {}
        async with httpx.AsyncClient() as client:
            response                    = await client.post(
                f"https://{self.EndPoint}",
                headers                 = headers,
                data                    = payload.encode("utf-8")
            )
            data                        = json.loads(response.text)
            # print(json.dumps(data,indent=4, ensure_ascii=False))
        return data

