############################################################
# Global
############################################################

variable "businessunit" {
  type        = string
  description = "Busniess Unit"
}
variable "region" {
  type        = string
  description = "Region"
}

variable "department" {
  type        = string
  description = "Department"
}

variable "owner" {
  type        = string
  description = "Owner"
}

variable "application" {
  type        = string
  description = "Application"
}

############################################################
# Key Rotation State Machine
############################################################

variable "target_state_machine_name" {
  type = string
  description = "Name of the target state machine to be triggered"
}

variable "target_state_machine_input" {
  type = any
  description = "State Machine JSON input"
}
############################################################
# IAM
############################################################

variable "eventbridge_scheduler_role_name" {
  type = string
  description = "Name of the event bridge scheduler role"
}

variable "eventbridge_scheduler_policy_name" {
  type = string
  description = "Name of the event bridge scheduler policy"
}

variable "eventbridge_scheduler_policy_description" {
  type = string
  description = "Description of the event bridge scheduler policy"
}
############################################################
# EventBridge Scheduler
############################################################

variable "event_bridge_scheduler_name" {
  type = string
  description = "Name of the event bridge scheduler"
}

variable "schedule_expression" {
  type = string
  description = "Schedule expression of the event bridge scheduler"
}