import pulumi
import pulumi_aws as aws
import json
import os

NEW_RELIC_LICENSE_KEY = os.environ.get("NEW_RELIC_LICENSE_KEY")
NEW_RELIC_ACCOUNT_ID = os.environ.get("NEW_RELIC_ACCOUNT_ID")
NEW_RELIC_LAYER_ARN = "arn:aws:lambda:us-east-1:451483290750:layer:NewRelicPython39:99"  # Replace <region> and version as needed

lambda_role = aws.iam.Role("lambda-role",
    assume_role_policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Action": "sts:AssumeRole",
            "Principal": {"Service": "lambda.amazonaws.com"},
            "Effect": "Allow"
        }]
    })
)

bedrock_policy = aws.iam.RolePolicy("bedrock-policy",
    role=lambda_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "bedrock:InvokeModel",
                "bedrock:ListFoundationModels",
                "bedrock:InvokeModelWithResponseStream",
                "bedrock:GetInferenceProfile",
                "bedrock:ListInferenceProfiles"
            ],
            # "Resource": "*"
            "Resource": [
				"arn:aws:bedrock:*::foundation-model/*",
                "arn:aws:bedrock:*::inference-profile/*",
			]
        },
        {
            "Sid": "MarketplaceAccess",
            "Effect": "Allow",
            "Action": [
                "aws-marketplace:ViewSubscriptions",
                "aws-marketplace:Subscribe"
            ],
            "Resource": "*",
            "Condition": {
                "StringEquals": {
                    "aws:CalledViaLast": "bedrock.amazonaws.com"
                }
            }
        }
        ]
    })
)

cloudwatch_policy = aws.iam.RolePolicy("cloudwatch-policy",
    role=lambda_role.id,
    policy=json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:*:*:*"
        }]
    })
)

chat_function = aws.lambda_.Function("chat-bedrock-ai-demo",
    role=lambda_role.arn,
    runtime="python3.9",
    handler="newrelic_lambda_wrapper.handler",  # Direct handler
    code=pulumi.AssetArchive({".": pulumi.FileArchive("../apps/backend")}),
    layers=[NEW_RELIC_LAYER_ARN],
    # tags={
    #     "NR.Apm.Lambda.Mode": "true"  # Enable New Relic APM Lambda Mode
    # },
    environment={
        "variables": {
            # Basic New Relic Configuration
            "NEW_RELIC_LICENSE_KEY": NEW_RELIC_LICENSE_KEY,
            "NEW_RELIC_ACCOUNT_ID": NEW_RELIC_ACCOUNT_ID,
            "NEW_RELIC_LAMBDA_HANDLER": "app.handler",
            
            # Enhanced telemetry collection
            "NEW_RELIC_EXTENSION_SEND_FUNCTION_LOGS": "true",
            "NEW_RELIC_DISTRIBUTED_TRACING_ENABLED": "true",
            "NEW_RELIC_SERVERLESS_MODE_ENABLED": "true",
            "NEW_RELIC_EXTENSION_LOGS_ENABLED": "true",
            
            # Lambda extension settings
            "NEW_RELIC_LAMBDA_EXTENSION_ENABLED": "true",
            "NEW_RELIC_TELEMETRY_ENABLED": "true",
            
            # Advanced logging configuration
            "NEW_RELIC_LOG_LEVEL": "INFO",
            "NEW_RELIC_EXTENSION_LOG_LEVEL": "INFO",
            
            # AI observability settings
            "NEW_RELIC_AI_MONITORING_ENABLED": "true",
            "NEW_RELIC_AI_MONITORING_STREAMING_ENABLED": "true",
            "NEW_RELIC_AI_MONITORING_RECORD_CONTENT_ENABLED": "true",
            
            # Metadata for better categorization
            # "NEW_RELIC_APP_NAME": "AI-Bedrock-Serverless",
            # "NEW_RELIC_METADATA_DEPLOYMENT": "Pulumi",
            # "NEW_RELIC_METADATA_SERVICE": "AI-Generation-Service",

            # "NEW_RELIC_APM_LAMBDA_MODE": "true"
        }
    },
    memory_size=256,
    timeout=300
)

function_url = aws.lambda_.FunctionUrl("chat-url",
    function_name=chat_function.name,
    authorization_type="NONE",
    invoke_mode="RESPONSE_STREAM",  # Enable response streaming
    cors={
        "allow_credentials": True,
        "allow_origins": ["*"],
        "allow_methods": ["*"],
        "allow_headers": ["*"]
    }
)

# S3 bucket for hosting the React frontend
frontend_bucket = aws.s3.Bucket("frontend-bucket")

# S3 bucket website configuration
bucket_website = aws.s3.BucketWebsiteConfiguration("frontend-bucket-website",
    bucket=frontend_bucket.id,
    index_document={
        "suffix": "index.html"
    },
    error_document={
        "key": "index.html"
    }
)

# Configure bucket for public read access
bucket_policy = aws.s3.BucketPolicy("frontend-bucket-policy",
    bucket=frontend_bucket.id,
    policy=pulumi.Output.all(frontend_bucket.arn).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [{
                "Effect": "Allow",
                "Principal": "*",
                "Action": "s3:GetObject",
                "Resource": f"{args[0]}/*"
            }]
        })
    )
)

# Block public ACLs but allow bucket policy
bucket_public_access_block = aws.s3.BucketPublicAccessBlock("frontend-bucket-pab",
    bucket=frontend_bucket.id,
    block_public_acls=True,
    block_public_policy=False,
    ignore_public_acls=True,
    restrict_public_buckets=False
)

# CloudFront Origin Access Control
oac = aws.cloudfront.OriginAccessControl("frontend-oac",
    name="Frontend OAC",
    origin_access_control_origin_type="s3",
    signing_behavior="always",
    signing_protocol="sigv4"
)

# CloudFront distribution
distribution = aws.cloudfront.Distribution("frontend-distribution",
    origins=[{
        "domain_name": frontend_bucket.bucket_domain_name,
        "origin_id": "S3-frontend",
        "origin_access_control_id": oac.id,
        "s3_origin_config": {
            "origin_access_identity": ""
        }
    }],
    enabled=True,
    is_ipv6_enabled=True,
    default_root_object="index.html",
    default_cache_behavior={
        "allowed_methods": ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"],
        "cached_methods": ["GET", "HEAD"],
        "target_origin_id": "S3-frontend",
        "compress": True,
        "viewer_protocol_policy": "redirect-to-https",
        "forwarded_values": {
            "query_string": False,
            "cookies": {"forward": "none"}
        },
        "min_ttl": 0,
        "default_ttl": 3600,
        "max_ttl": 86400
    },
    # Handle React Router (SPA) - redirect 404s to index.html
    custom_error_responses=[{
        "error_code": 404,
        "response_code": 200,
        "response_page_path": "/index.html"
    }],
    restrictions={
        "geo_restriction": {
            "restriction_type": "none"
        }
    },
    viewer_certificate={
        "cloudfront_default_certificate": True
    }
)

# Update bucket policy to allow CloudFront access
cloudfront_bucket_policy = aws.s3.BucketPolicy("cloudfront-bucket-policy",
    bucket=frontend_bucket.id,
    policy=pulumi.Output.all(frontend_bucket.arn, distribution.arn).apply(
        lambda args: json.dumps({
            "Version": "2012-10-17",
            "Statement": [
                {
                    "Effect": "Allow",
                    "Principal": {
                        "Service": "cloudfront.amazonaws.com"
                    },
                    "Action": "s3:GetObject",
                    "Resource": f"{args[0]}/*",
                    "Condition": {
                        "StringEquals": {
                            "AWS:SourceArn": args[1]
                        }
                    }
                }
            ]
        })
    ),
    opts=pulumi.ResourceOptions(depends_on=[bucket_public_access_block])
)

# Export the Function URL for easy access
pulumi.export("function_url", function_url.function_url)
# Export frontend URLs
pulumi.export("bucket_name", frontend_bucket.id)
pulumi.export("bucket_website_url", frontend_bucket.website_endpoint)
pulumi.export("cloudfront_url", distribution.domain_name)
pulumi.export("cloudfront_distribution_id", distribution.id)