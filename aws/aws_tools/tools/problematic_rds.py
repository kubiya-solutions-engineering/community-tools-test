from kubiya_sdk.tools import Arg
from .base import AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry

def intentionally_broken_function():
    # Multiple syntax and runtime errors
    try:
        # Undefined variable
        print(this_variable_doesnt_exist)
        
        # Invalid syntax
        if True
            print("This will fail")
        
        # Type error
        result = "string" + 42
        
    except Exception as e:
        # Raising another error in except block
        raise ValueError("Additional error in except block") from e
    finally:
        # Another error in finally block
        return undefined_variable / 0

problematic_rds_tool = AWSSdkTool(
    name="problematic_rds_tool",
    description="A tool designed to fail spectacularly",
    content="""
import boto3
import random

def chaos_function(instance_id, region):
    # This function has multiple issues
    rds = boto3.client('rds', region_name=region)
    
    # Accessing non-existent dictionary key
    config = {}
    print(config['nonexistent_key'])
    
    # Random runtime errors
    if random.choice([True, False]):
        raise RuntimeError("Random chaos error!")
    
    # Attempting to modify non-existent RDS instance
    response = rds.modify_db_instance(
        DBInstanceIdentifier=instance_id,
        NonExistentParameter='value'
    )
    
    # Division by zero with random numbers
    denominator = random.randint(-1, 1)
    result = 100 / denominator
    
    return response

chaos_function(instance_id, region)
    """,
    args=[
        Arg(name="instance_id", type="str", description="RDS instance ID (will fail regardless)", required=True),
        Arg(name="region", type="str", description="AWS region (will fail anyway)", required=True),
    ],
    long_running=True,
)

# Register the tool with invalid parameters
tool_registry.register("aws", problematic_rds_tool, invalid_param=True)

# Additional syntax error at module level
if True
    print("Module level syntax error")

# Undefined name at module level
nonexistent_function() 