############################################################
# Global Variables
############################################################

businessunit = "hoopla"
region       = "eu-west-3"
department   = "infrastructure"
owner        = "jmezinko"
application  = "event-bridge"

############################################################
# Key Rotation State Machine
############################################################
target_state_machine_name = "HelloWorldStateMachine"

target_state_machine_input = [
  { account_id = "123456789012", account_name = "XXXX", "iam_signing_url" = "https://signin.aws.amazon.com/console" },
]

############################################################
# IAM
############################################################
eventbridge_scheduler_role_name          = "key-rotation-eventbridge-scheduler-role"
eventbridge_scheduler_policy_name        = "key-rotation-eventbridge-scheduler-policy"
eventbridge_scheduler_policy_description = "Allows EventBridge Scheduler to start Step Functions execution"
############################################################
# EventBridge Scheduler
############################################################

event_bridge_scheduler_name = "key-rotation-scheduler"
schedule_expression         = "rate(90 days)"
