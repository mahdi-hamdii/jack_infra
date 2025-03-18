############################################################
# Key Rotation State Machine
############################################################

data "aws_sfn_state_machine" "key_rotation_state_machine" {
  name = var.target_state_machine_name
}

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
      Effect = "Allow"
      Action = "states:StartExecution"
      Resource = data.aws_sfn_state_machine.key_rotation_state_machine.arn
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
  name = var.event_bridge_scheduler_name

  flexible_time_window {
    mode = "OFF"
  }

  schedule_expression = var.schedule_expression

  target {
    arn      = data.aws_sfn_state_machine.key_rotation_state_machine.arn
    role_arn = aws_iam_role.eventbridge_scheduler_role.arn

    input = jsonencode(var.target_state_machine_input)
  }
}