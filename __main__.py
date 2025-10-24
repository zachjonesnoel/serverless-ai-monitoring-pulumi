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
    code=pulumi.AssetArchive({".": pulumi.FileArchive("./src")}),
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

# Export the Function URL for easy access
pulumi.export("function_url", function_url.function_url)