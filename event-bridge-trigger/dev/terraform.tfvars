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
target_state_machine_arn = "arn:aws:states:eu-west-3:123456789012:stateMachine:HelloWorldStateMachine"

############################################################
# IAM
############################################################
eventbridge_scheduler_role_name          = "key-rotation-eventbridge-scheduler-role"
eventbridge_scheduler_policy_name        = "key-rotation-eventbridge-scheduler-policy"
eventbridge_scheduler_policy_description = "Allows EventBridge Scheduler to start Step Functions execution"

############################################################
# EventBridge Scheduler
############################################################

event_bridge_schedulers = {
  # Test setup
  test = {
    event_bridge_scheduler_name = "key-rotation-scheduler-test"
    start_date                  = "2025-07-01T10:00:00Z" # To prevent the scheduler from running immediately
    schedule_expression         = "rate(90 days)"
    target_state_machine_input = [
      { account_id = "123456789012", account_name = "XXXX", iam_signing_url = "https://signin.aws.amazon.com/console" },
    ],
  }

  # Prod setup (after 3 hours)
  prod = {
    event_bridge_scheduler_name = "key-rotation-scheduler"
    start_date                  = "2025-07-01T13:00:00Z" # To prevent the scheduler from running immediately
    schedule_expression         = "rate(90 days)"
    target_state_machine_input = [
      { account_id = "222333444333", account_name = "XXXX", iam_signing_url = "https://signin.aws.amazon.com/console" },
      { account_id = "444556632212", account_name = "XXXX", iam_signing_url = "https://signin.aws.amazon.com/console" },
    ],
  }
}
