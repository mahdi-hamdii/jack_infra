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
# just update the arn to the test state machine
target_state_machine_arn = "arn:aws:states:eu-west-3:123456789012:stateMachine:HelloWorldStateMachine"

############################################################
# IAM
############################################################
eventbridge_scheduler_role_name          = "key-rotation-eventbridge-scheduler-role-test"
eventbridge_scheduler_policy_name        = "key-rotation-eventbridge-scheduler-policy-test"
eventbridge_scheduler_policy_description = "Allows EventBridge Scheduler to start Step Functions execution"

############################################################
# EventBridge Scheduler
############################################################

event_bridge_schedulers = {
  # Test setup
  test = {
    event_bridge_scheduler_name = "key-rotation-scheduler-test"
    schedule_expression         = "rate(90 days)"
    target_state_machine_input = [
      { account_id = "123456789012", account_name = "XXXX", iam_signing_url = "https://signin.aws.amazon.com/console" },
    ],
  }

}
