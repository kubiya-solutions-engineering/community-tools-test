from kubiya_sdk.tools import Arg
from .base import AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

def test_problematic_function():
    # This will raise an exception due to undefined variable
    print(undefined_variable)

s3_problematic_tool = AWSSdkTool(
    name="s3_problematic_tool",
    description="A tool designed to fail for testing",
    content="""
import boto3

def problematic_function(bucket_name):
    # This function has multiple issues that will cause failures
    s3 = boto3.client('s3')
    
    # Trying to access non-existent bucket without proper error handling
    response = s3.list_objects_v2(Bucket=bucket_name)
    
    # Undefined variable reference
    print(nonexistent_variable)
    
    # Division by zero
    result = 100 / 0
    
    return response

problematic_function(bucket_name)
    """,
    args=[
        Arg(name="bucket_name", type="str", description="Name of the bucket (will fail anyway)", required=True),
    ],
    long_running=True,
)

tool_registry.register("aws", s3_problematic_tool)