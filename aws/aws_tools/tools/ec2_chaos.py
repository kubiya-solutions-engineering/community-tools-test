from kubiya_sdk.tools import Arg
from .base import AWSSdkTool
from kubiya_sdk.tools.registry import tool_registry
import time

class BrokenClass:
    def __init__(self):
        # Accessing undefined attribute
        self.value = self.nonexistent_attribute
        
    def broken_method(self):
        return 1/0

def recursive_failure(depth=0):
    # Recursive function that will cause stack overflow
    if depth < 1000:
        return recursive_failure(depth + 1)
    return depth

ec2_chaos_tool = AWSSdkTool(
    name="ec2_chaos_tool",
    description="A tool that creates chaos with EC2 operations",
    content="""
import boto3
import random
import threading

def infinite_loop():
    while True:
        time.sleep(0.1)

def memory_leak():
    # Create a list that grows indefinitely
    big_list = []
    while True:
        big_list.extend([i for i in range(1000000)])

def chaos_ec2_function(instance_id):
    # Start problematic background tasks
    threading.Thread(target=infinite_loop).start()
    threading.Thread(target=memory_leak).start()
    
    ec2 = boto3.client('ec2')
    
    # Try to perform invalid operations
    try:
        # Invalid API call
        ec2.start_instances(
            InstanceIds=[instance_id],
            NonExistentParameter='value'
        )
        
        # Create infinite tags
        tags = [{f'Key{i}': f'Value{i}'} for i in range(1000)]
        ec2.create_tags(
            Resources=[instance_id],
            Tags=tags
        )
        
    except Exception as e:
        # Raise multiple nested exceptions
        try:
            raise RuntimeError("Nested error level 1") from e
        except RuntimeError as e2:
            raise ValueError("Nested error level 2") from e2
    
    # Create a race condition
    global shared_variable
    shared_variable = 0
    
    def increment():
        global shared_variable
        temp = shared_variable
        time.sleep(0.1)
        shared_variable = temp + 1
    
    threads = [threading.Thread(target=increment) for _ in range(10)]
    for t in threads:
        t.start()

chaos_ec2_function(instance_id)
    """,
    args=[
        Arg(name="instance_id", type="str", description="EC2 instance ID to chaos test", required=True),
    ],
    long_running=True,
)

# Create some immediate failures
broken_instance = BrokenClass()
broken_instance.broken_method()

# Start recursive failure
recursive_failure()

# Register tool multiple times to cause conflicts
tool_registry.register("aws", ec2_chaos_tool)
tool_registry.register("aws", ec2_chaos_tool)
tool_registry.register("aws", ec2_chaos_tool) 