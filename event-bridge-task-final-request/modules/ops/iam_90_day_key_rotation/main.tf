# Don't change anything of your existing code

################## Solution 1 #######################@

## Test config
module "event_bridge_test" {
  source = "../event_bridge"

  target_state_machine_arn                 = "arn:aws:states:eu-west-3:437781412181:stateMachine:HelloWorldStateMachine"
  eventbridge_scheduler_role_name          = "key-rotation-eventbridge-scheduler-role-test"
  eventbridge_scheduler_policy_name        = "key-rotation-eventbridge-scheduler-policy-test"
  eventbridge_scheduler_policy_description = "Allows EventBridge Scheduler to start Step Functions execution for test account"
  event_bridge_schedulers = {
    test = {
      event_bridge_scheduler_name = "key-rotation-scheduler-test"
      schedule_expression         = "rate(90 days)"
      target_state_machine_input = [
        { account_id = "123456789012", account_name = "XXXX", iam_signing_url = "https://signin.aws.amazon.com/console" },
      ],
    }
  }

}


## Prod config
module "event_bridge_prod" {
  source = "../event_bridge"

  target_state_machine_arn                 = "arn:aws:states:eu-west-3:437781412181:stateMachine:HelloWorldStateMachine"
  eventbridge_scheduler_role_name          = "key-rotation-eventbridge-scheduler-role"
  eventbridge_scheduler_policy_name        = "key-rotation-eventbridge-scheduler-policy"
  eventbridge_scheduler_policy_description = "Allows EventBridge Scheduler to start Step Functions execution"
  event_bridge_schedulers = {
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

}


################## Solution 2 #######################@

locals {
  event_bridge_scheduler = {
    test_accounts = {
      target_state_machine_arn                 = "arn:aws:states:eu-west-3:437781412181:stateMachine:HelloWorldStateMachine"
      eventbridge_scheduler_role_name          = "key-rotation-eventbridge-scheduler-role-test"
      eventbridge_scheduler_policy_name        = "key-rotation-eventbridge-scheduler-policy-test"
      eventbridge_scheduler_policy_description = "Allows EventBridge Scheduler to start Step Functions execution for test account"
      event_bridge_schedulers = {
        test = {
          event_bridge_scheduler_name = "key-rotation-scheduler-test"
          schedule_expression         = "rate(90 days)"
          target_state_machine_input = [
            { account_id = "123456789012", account_name = "XXXX", iam_signing_url = "https://signin.aws.amazon.com/console" },
          ],
        }
      }
    }

    prod_accounts = {
      target_state_machine_arn                 = "arn:aws:states:eu-west-3:437781412181:stateMachine:HelloWorldStateMachine"
      eventbridge_scheduler_role_name          = "key-rotation-eventbridge-scheduler-role"
      eventbridge_scheduler_policy_name        = "key-rotation-eventbridge-scheduler-policy"
      eventbridge_scheduler_policy_description = "Allows EventBridge Scheduler to start Step Functions execution"
      event_bridge_schedulers = {
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
    }
  }
}

module "event_bridge_prod" {
  source   = "../event_bridge"
  for_each = local.event_bridge_scheduler

  target_state_machine_arn                 = each.value.target_state_machine_arn
  eventbridge_scheduler_role_name          = each.value.eventbridge_scheduler_role_name
  eventbridge_scheduler_policy_name        = each.value.eventbridge_scheduler_policy_name
  eventbridge_scheduler_policy_description = each.value.eventbridge_scheduler_policy_description
  event_bridge_schedulers                  = each.value.event_bridge_schedulers
}
