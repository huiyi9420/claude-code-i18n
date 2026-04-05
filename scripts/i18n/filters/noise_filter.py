"""Noise filter for Claude Code i18n string extraction.

Rejects code-like strings that are not user-facing UI text.
Migrated from v3.0 localize.py NOISE_KW list.
"""

import re

NOISE_KW = [
    # Third-party library internals
    "azure", "msal", "oauth2?", "grpc", "protobuf", "aws ", "amazon", "google cloud",
    "websocket", "sec-websocket", "rsv[123]", "opcode", "mask must", "fin must",
    "acquiretoken", "loggerprovider", "meterprovider",
    "codegen", "bigint", "base64значение", "xmlзначение",
    "www-authenticate", "managed identity", "instance metadata",
    "edms_", "edoc_", "access_rights", "cloud instance discovery",
    "formdata", "multipart", "telemetry", "semantic conventions",
    "suppressed", "disposal", "disposable", "bridge client", "payload length",
    "block sequence", "anchor", "yaml", "redirect uri", "credential source",
    "subject token", "signature verification", "pkcs", "asn.1",
    "rfc-3339", "int64 buffer", "private member", "fips", "dualstack", "dualstack",
    "s3 ", "ec2 ", "iam ", "lambda ", "cloudfront", "route53",
    "dynamodb", "kinesis", "sns ", "sqs ", "elasticache",
    "protocol buffer", "httprequest", "x-amz-",
    "rfc 3986", "rfc 6749", "rfc 723",
    # Programming language / protocol keywords
    "\\.proto", "utf-8", "cors", "content-type",
    # Irrelevant content
    "christmas carol", "game of thrones", "ted talk", "yoga class",
    "soccer match", "marathon", "transatlantic", "world cup",
    "inform 7", "jboss", "arcgis", "bigquery",
]

NOISE_RE = re.compile("|".join(NOISE_KW), re.IGNORECASE)


def is_noise(s: str) -> bool:
    """Check if a string matches any noise pattern.

    Args:
        s: The string to check.

    Returns:
        True if the string matches a noise pattern (should be excluded).
    """
    return bool(NOISE_RE.search(s))
