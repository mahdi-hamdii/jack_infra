############################################################
# IAM
############################################################

# IAM Role for EventBridge to trigger Step Functions
resource "aws_iam_role" "eventbridge_scheduler_role" {
  name = var.eventbridge_scheduler_role_name

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect = "Allow"
      Principal = {
        Service = "scheduler.amazonaws.com"
      }
      Action = "sts:AssumeRole"
    }]
  })
}

# IAM Policy for EventBridge Scheduler to start Step Functions execution
resource "aws_iam_policy" "eventbridge_scheduler_policy" {
  name        = var.eventbridge_scheduler_policy_name
  description = var.eventbridge_scheduler_policy_description

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Effect   = "Allow"
      Action   = "states:StartExecution"
      Resource = var.target_state_machine_arn
    }]
  })
}

# Attach the IAM Policy to the Role
resource "aws_iam_role_policy_attachment" "eventbridge_scheduler_policy_attach" {
  policy_arn = aws_iam_policy.eventbridge_scheduler_policy.arn
  role       = aws_iam_role.eventbridge_scheduler_role.name
}


############################################################
# EventBridge Scheduler to trigger Step Functions
############################################################

resource "aws_scheduler_schedule" "key_rotation_scheduler" {
  for_each = var.event_bridge_schedulers
  name     = each.value.event_bridge_scheduler_name

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = each.value.schedule_expression
  start_date          = lookup(each.value, "start_date", null)

  target {
    arn      = var.target_state_machine_arn
    role_arn = aws_iam_role.eventbridge_scheduler_role.arn

    input = jsonencode(each.value.target_state_machine_input)
  }
}
