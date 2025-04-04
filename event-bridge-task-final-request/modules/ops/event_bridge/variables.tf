############################################################
# Key Rotation State Machine
############################################################

variable "target_state_machine_arn" {
  type        = string
  description = "arn of the target state machine to be triggered"
}

############################################################
# IAM
############################################################

variable "eventbridge_scheduler_role_name" {
  type        = string
  description = "Name of the event bridge scheduler role"
}

variable "eventbridge_scheduler_policy_name" {
  type        = string
  description = "Name of the event bridge scheduler policy"
}

variable "eventbridge_scheduler_policy_description" {
  type        = string
  description = "Description of the event bridge scheduler policy"
}
############################################################
# EventBridge Scheduler
############################################################

variable "event_bridge_schedulers" {
  type = map(object({
    event_bridge_scheduler_name = string
    schedule_expression         = string
    start_date                  = optional(any, null)
    target_state_machine_input  = any
  }))
  description = "Map of event bridge schedulers configuration"
}


