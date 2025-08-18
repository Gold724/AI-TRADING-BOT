# Add metadata as comments
        join_str = ' \\
  '
        curl_command = join_str.join(curl_parts)
        metadata = f"#!/bin/bash\n# Trade Request Captured: {trade_request.timestamp}\n# Confidence Score: {trade_request.confidence_score:.2f}\n# Payload Type: {trade_request.payload_type}\n# Session ID: {trade_request.session_id}\n\n"
        curl_command = metadata + curl_command
