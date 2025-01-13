from kubiya_sdk.tools import Arg
from .base import AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry
import sys
import gc

# Force garbage collection to cause potential issues
gc.collect()
gc.set_debug(gc.DEBUG_LEAK | gc.DEBUG_STATS | gc.DEBUG_UNCOLLECTABLE)

class LeakyClass:
    def __init__(self):
        # Create circular reference
        self.other = LeakyClass2(self) if 'LeakyClass2' in globals() else None
        # Grow the memory indefinitely
        self.data = [object() for _ in range(1000000)]

class LeakyClass2:
    def __init__(self, ref):
        self.ref = ref
        # More memory growth
        self.more_data = [object() for _ in range(1000000)]

# Create memory leak
leaky_objects = [LeakyClass() for _ in range(10)]

def crash_python():
    # Attempt to modify system recursion limit
    sys.setrecursionlimit(1000000)
    
    def recursive_dict():
        d = {}
        d['self'] = d
        return d
    
    # Create recursive dictionary
    return str(recursive_dict())

iam_chaos_tool = AWSSdkTool(
    name="iam_chaos_tool",
    description="A tool that creates authentication and IAM chaos",
    content="""
import boto3
import json
import threading
import random
import time

def create_invalid_policy():
    # Create an invalid IAM policy document
    return {
        "Version": "Invalid-Version",
        "Statement": [
            {
                "Effect": "InvalidEffect",
                "Action": ["*"],
                "Resource": "not-a-valid-arn",
                "Condition": {"InvalidCondition": {"aws:InvalidKey": "Value"}}
            }
        ] * 1000  # Multiply to create oversized policy
    }

def chaos_iam_function(role_name):
    # Try multiple regions simultaneously
    regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1']
    
    def region_chaos(region):
        try:
            # Create clients with invalid credentials
            iam = boto3.client('iam', 
                region_name=region,
                aws_access_key_id='INVALID_KEY',
                aws_secret_access_key='INVALID_SECRET')
            
            # Attempt invalid operations
            policy_document = json.dumps(create_invalid_policy())
            
            # Try to create role with invalid policy
            iam.create_role(
                RoleName=role_name,
                AssumeRolePolicyDocument=policy_document,
                Tags=[{'Key': str(i), 'Value': 'v'*256} for i in range(1000)]
            )
            
            # Attempt to assume role with invalid credentials
            sts = boto3.client('sts', region_name=region)
            sts.assume_role(
                RoleArn=f'arn:aws:iam::INVALID:role/{role_name}',
                RoleSessionName='x'*1000
            )
            
        except Exception as e:
            # Raise nested exceptions with large error messages
            error_msg = 'e' * 1000000
            raise RuntimeError(error_msg) from e
    
    # Start threads for each region
    threads = []
    for region in regions:
        thread = threading.Thread(target=region_chaos, args=(region,))
        thread.daemon = True
        thread.start()
        threads.append(thread)
    
    # Wait for threads while consuming CPU
    while any(t.is_alive() for t in threads):
        # Perform CPU-intensive operation
        [random.random() for _ in range(1000000)]
        time.sleep(0.1)

chaos_iam_function(role_name)
    """,
    args=[
        Arg(name="role_name", type="str", description="IAM role name to chaos test", required=True),
    ],
    long_running=True,
)

# Attempt to crash Python interpreter
crash_result = crash_python()

# Register tool with invalid parameters
for i in range(100):
    tool_registry.register(
        "aws", 
        iam_chaos_tool, 
        **{f'invalid_param_{i}': 'x' * 1000000}
    )

# Force garbage collection again
gc.collect()

# Create more memory pressure
large_data = ['x' * 1000000 for _ in range(1000)] 