{{/*
Expand the name of the chart.
*/}}
{{- define "trading-sentinel.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
We truncate at 63 chars because some Kubernetes name fields are limited to this (by the DNS naming spec).
If release name contains chart name it will be used as a full name.
*/}}
{{- define "trading-sentinel.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "trading-sentinel.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "trading-sentinel.labels" -}}
helm.sh/chart: {{ include "trading-sentinel.chart" . }}
{{ include "trading-sentinel.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: trading-sentinel
app.kubernetes.io/component: application
{{- end }}

{{/*
Selector labels
*/}}
{{- define "trading-sentinel.selectorLabels" -}}
app.kubernetes.io/name: {{ include "trading-sentinel.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "trading-sentinel.serviceAccountName" -}}
{{- if .Values.security.serviceAccount.create }}
{{- default (include "trading-sentinel.fullname" .) .Values.security.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.security.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Create the Docker image reference
*/}}
{{- define "trading-sentinel.image" -}}
{{- $registry := .Values.image.registry -}}
{{- $repository := .Values.image.repository -}}
{{- $tag := .Values.image.tag | default .Chart.AppVersion -}}
{{- if .Values.global.imageRegistry -}}
{{- $registry = .Values.global.imageRegistry -}}
{{- end -}}
{{- if $registry -}}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else -}}
{{- printf "%s:%s" $repository $tag -}}
{{- end -}}
{{- end }}

{{/*
Database configuration helpers
*/}}
{{- define "trading-sentinel.databaseHost" -}}
{{- if .Values.postgresql.enabled -}}
{{- printf "%s-postgresql" (include "trading-sentinel.fullname" .) -}}
{{- else if .Values.externalDatabase.enabled -}}
{{- .Values.externalDatabase.host -}}
{{- else -}}
{{- "localhost" -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.databasePort" -}}
{{- if .Values.postgresql.enabled -}}
{{- "5432" -}}
{{- else if .Values.externalDatabase.enabled -}}
{{- .Values.externalDatabase.port | toString -}}
{{- else -}}
{{- "5432" -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.databaseName" -}}
{{- if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.database -}}
{{- else if .Values.externalDatabase.enabled -}}
{{- .Values.externalDatabase.database -}}
{{- else -}}
{{- "trading_sentinel" -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.databaseUser" -}}
{{- if .Values.postgresql.enabled -}}
{{- .Values.postgresql.auth.username -}}
{{- else if .Values.externalDatabase.enabled -}}
{{- .Values.externalDatabase.username -}}
{{- else -}}
{{- "trading_user" -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.databaseSecretName" -}}
{{- if .Values.postgresql.enabled -}}
{{- printf "%s-postgresql" (include "trading-sentinel.fullname" .) -}}
{{- else if .Values.externalDatabase.existingSecret -}}
{{- .Values.externalDatabase.existingSecret -}}
{{- else -}}
{{- include "trading-sentinel.fullname" . -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.databaseSecretPasswordKey" -}}
{{- if .Values.postgresql.enabled -}}
{{- "password" -}}
{{- else if .Values.externalDatabase.existingSecretPasswordKey -}}
{{- .Values.externalDatabase.existingSecretPasswordKey -}}
{{- else -}}
{{- "database-password" -}}
{{- end -}}
{{- end -}}

{{/*
Redis configuration helpers
*/}}
{{- define "trading-sentinel.redisHost" -}}
{{- if .Values.redis.enabled -}}
{{- printf "%s-redis-master" (include "trading-sentinel.fullname" .) -}}
{{- else if .Values.externalRedis.enabled -}}
{{- .Values.externalRedis.host -}}
{{- else -}}
{{- "localhost" -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.redisPort" -}}
{{- if .Values.redis.enabled -}}
{{- "6379" -}}
{{- else if .Values.externalRedis.enabled -}}
{{- .Values.externalRedis.port | toString -}}
{{- else -}}
{{- "6379" -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.redisSecretName" -}}
{{- if .Values.redis.enabled -}}
{{- printf "%s-redis" (include "trading-sentinel.fullname" .) -}}
{{- else if .Values.externalRedis.existingSecret -}}
{{- .Values.externalRedis.existingSecret -}}
{{- else -}}
{{- include "trading-sentinel.fullname" . -}}
{{- end -}}
{{- end -}}

{{- define "trading-sentinel.redisSecretPasswordKey" -}}
{{- if .Values.redis.enabled -}}
{{- "redis-password" -}}
{{- else if .Values.externalRedis.existingSecretPasswordKey -}}
{{- .Values.externalRedis.existingSecretPasswordKey -}}
{{- else -}}
{{- "redis-password" -}}
{{- end -}}
{{- end -}}

{{/*
Environment variables for database connection
*/}}
{{- define "trading-sentinel.databaseEnv" -}}
- name: DATABASE_HOST
  value: {{ include "trading-sentinel.databaseHost" . | quote }}
- name: DATABASE_PORT
  value: {{ include "trading-sentinel.databasePort" . | quote }}
- name: DATABASE_NAME
  value: {{ include "trading-sentinel.databaseName" . | quote }}
- name: DATABASE_USER
  value: {{ include "trading-sentinel.databaseUser" . | quote }}
- name: DATABASE_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "trading-sentinel.databaseSecretName" . }}
      key: {{ include "trading-sentinel.databaseSecretPasswordKey" . }}
- name: DATABASE_URL
  value: postgresql://$(DATABASE_USER):$(DATABASE_PASSWORD)@$(DATABASE_HOST):$(DATABASE_PORT)/$(DATABASE_NAME)
{{- end -}}

{{/*
Environment variables for Redis connection
*/}}
{{- define "trading-sentinel.redisEnv" -}}
- name: REDIS_HOST
  value: {{ include "trading-sentinel.redisHost" . | quote }}
- name: REDIS_PORT
  value: {{ include "trading-sentinel.redisPort" . | quote }}
{{- if or .Values.redis.auth.enabled .Values.externalRedis.password }}
- name: REDIS_PASSWORD
  valueFrom:
    secretKeyRef:
      name: {{ include "trading-sentinel.redisSecretName" . }}
      key: {{ include "trading-sentinel.redisSecretPasswordKey" . }}
- name: REDIS_URL
  value: redis://:$(REDIS_PASSWORD)@$(REDIS_HOST):$(REDIS_PORT)/0
{{- else }}
- name: REDIS_URL
  value: redis://$(REDIS_HOST):$(REDIS_PORT)/0
{{- end }}
{{- end -}}

{{/*
Common environment variables
*/}}
{{- define "trading-sentinel.env" -}}
{{- include "trading-sentinel.databaseEnv" . }}
{{- include "trading-sentinel.redisEnv" . }}
- name: APP_NAME
  value: {{ .Values.app.name | quote }}
- name: APP_VERSION
  value: {{ .Values.app.version | quote }}
- name: ENVIRONMENT
  value: {{ .Values.app.environment | quote }}
- name: LOG_LEVEL
  value: {{ .Values.app.logLevel | quote }}
- name: DEBUG
  value: {{ .Values.app.debug | quote }}
- name: API_PORT
  value: {{ .Values.app.api.port | quote }}
- name: API_WORKERS
  value: {{ .Values.app.api.workers | quote }}
- name: API_TIMEOUT
  value: {{ .Values.app.api.timeout | quote }}
{{- if .Values.app.websocket.enabled }}
- name: WEBSOCKET_ENABLED
  value: "true"
- name: WEBSOCKET_PORT
  value: {{ .Values.app.websocket.port | quote }}
- name: WEBSOCKET_MAX_CONNECTIONS
  value: {{ .Values.app.websocket.maxConnections | quote }}
{{- end }}
- name: MAX_ACCOUNTS
  value: {{ .Values.app.trading.maxAccounts | quote }}
- name: MAX_CONCURRENT_TRADES
  value: {{ .Values.app.trading.maxConcurrentTrades | quote }}
{{- if .Values.app.trading.riskManagement.enabled }}
- name: RISK_MANAGEMENT_ENABLED
  value: "true"
- name: MAX_DRAWDOWN
  value: {{ .Values.app.trading.riskManagement.maxDrawdown | quote }}
- name: MAX_DAILY_LOSS
  value: {{ .Values.app.trading.riskManagement.maxDailyLoss | quote }}
{{- end }}
{{- if .Values.monitoring.metrics.enabled }}
- name: METRICS_ENABLED
  value: "true"
- name: METRICS_PORT
  value: {{ .Values.monitoring.metrics.port | quote }}
- name: METRICS_PATH
  value: {{ .Values.monitoring.metrics.path | quote }}
{{- end }}
{{- if .Values.monitoring.jaeger.enabled }}
- name: JAEGER_AGENT_HOST
  value: {{ .Values.monitoring.jaeger.agent.host | quote }}
- name: JAEGER_AGENT_PORT
  value: {{ .Values.monitoring.jaeger.agent.port | quote }}
{{- end }}
- name: KUBERNETES_NAMESPACE
  valueFrom:
    fieldRef:
      fieldPath: metadata.namespace
- name: POD_NAME
  valueFrom:
    fieldRef:
      fieldPath: metadata.name
- name: POD_IP
  valueFrom:
    fieldRef:
      fieldPath: status.podIP
- name: NODE_NAME
  valueFrom:
    fieldRef:
      fieldPath: spec.nodeName
{{- end -}}

{{/*
Volume mounts
*/}}
{{- define "trading-sentinel.volumeMounts" -}}
{{- if .Values.persistence.enabled }}
{{- range $name, $config := .Values.persistence.volumes }}
{{- if $config.enabled }}
- name: {{ $name }}
  mountPath: {{ $config.mountPath }}
{{- end }}
{{- end }}
{{- end }}
- name: config
  mountPath: /app/config
  readOnly: true
{{- end -}}

{{/*
Resource limits and requests
*/}}
{{- define "trading-sentinel.resources" -}}
{{- $environment := .Values.app.environment -}}
{{- $resources := .Values.deployment.resources -}}
{{- if eq $environment "development" }}
{{- $resources = .Values.development.resources -}}
{{- else if eq $environment "staging" }}
{{- $resources = .Values.staging.resources -}}
{{- end }}
{{- with $resources }}
resources:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end -}}

{{/*
Pod Security Context
*/}}
{{- define "trading-sentinel.podSecurityContext" -}}
{{- if .Values.security.podSecurityStandards.enforce }}
securityContext:
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  fsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
{{- else }}
{{- with .Values.deployment.podSecurityContext }}
securityContext:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Container Security Context
*/}}
{{- define "trading-sentinel.securityContext" -}}
{{- if .Values.security.podSecurityStandards.enforce }}
securityContext:
  allowPrivilegeEscalation: false
  capabilities:
    drop:
    - ALL
  readOnlyRootFilesystem: true
  runAsNonRoot: true
  runAsUser: 1000
  runAsGroup: 1000
  seccompProfile:
    type: RuntimeDefault
{{- else }}
{{- with .Values.deployment.securityContext }}
securityContext:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Ingress annotations
*/}}
{{- define "trading-sentinel.ingressAnnotations" -}}
{{- $annotations := .Values.ingress.annotations -}}
{{- if .Values.app.environment == "production" }}
{{- $annotations = merge $annotations (dict "nginx.ingress.kubernetes.io/rate-limit" "1000" "nginx.ingress.kubernetes.io/rate-limit-window" "1m") -}}
{{- end }}
{{- with $annotations }}
annotations:
  {{- toYaml . | nindent 2 }}
{{- end }}
{{- end -}}

{{/*
Service Monitor labels
*/}}
{{- define "trading-sentinel.serviceMonitorLabels" -}}
labels:
  {{- include "trading-sentinel.labels" . | nindent 2 }}
  monitoring: prometheus
{{- end -}}

{{/*
Prometheus Rule labels
*/}}
{{- define "trading-sentinel.prometheusRuleLabels" -}}
labels:
  {{- include "trading-sentinel.labels" . | nindent 2 }}
  prometheus: kube-prometheus
  role: alert-rules
{{- end -}}

{{/*
Network Policy labels
*/}}
{{- define "trading-sentinel.networkPolicyLabels" -}}
labels:
  {{- include "trading-sentinel.labels" . | nindent 2 }}
  policy: network-security
{{- end -}}

{{/*
Backup job labels
*/}}
{{- define "trading-sentinel.backupJobLabels" -}}
labels:
  {{- include "trading-sentinel.labels" . | nindent 2 }}
  job-type: backup
{{- end -}}

{{/*
Validate configuration
*/}}
{{- define "trading-sentinel.validateConfig" -}}
{{- if and (not .Values.postgresql.enabled) (not .Values.externalDatabase.enabled) }}
{{- fail "Either postgresql.enabled or externalDatabase.enabled must be true" }}
{{- end }}
{{- if and (not .Values.redis.enabled) (not .Values.externalRedis.enabled) }}
{{- fail "Either redis.enabled or externalRedis.enabled must be true" }}
{{- end }}
{{- if and .Values.autoscaling.enabled (lt (.Values.autoscaling.minReplicas | int) 1) }}
{{- fail "autoscaling.minReplicas must be at least 1" }}
{{- end }}
{{- if and .Values.autoscaling.enabled (gt (.Values.autoscaling.minReplicas | int) (.Values.autoscaling.maxReplicas | int)) }}
{{- fail "autoscaling.minReplicas must be less than or equal to autoscaling.maxReplicas" }}
{{- end }}
{{- end -}}

{{/*
Generate TLS certificate
*/}}
{{- define "trading-sentinel.generateTLS" -}}
{{- $ca := genCA "trading-sentinel-ca" 365 }}
{{- $cert := genSignedCert "trading-sentinel.local" nil (list "trading-sentinel.local" "localhost") 365 $ca }}
tls.crt: {{ $cert.Cert | b64enc }}
tls.key: {{ $cert.Key | b64enc }}
ca.crt: {{ $ca.Cert | b64enc }}
{{- end -}}

{{/*
Generate random password
*/}}
{{- define "trading-sentinel.generatePassword" -}}
{{- randAlphaNum 32 | b64enc }}
{{- end -}}

{{/*
Get storage class
*/}}
{{- define "trading-sentinel.storageClass" -}}
{{- if .Values.global.storageClass }}
{{- .Values.global.storageClass }}
{{- else if .Values.persistence.storageClass }}
{{- .Values.persistence.storageClass }}
{{- else }}
{{- "" }}
{{- end }}
{{- end -}}

{{/*
Get image pull secrets
*/}}
{{- define "trading-sentinel.imagePullSecrets" -}}
{{- $secrets := list }}
{{- if .Values.global.imagePullSecrets }}
{{- $secrets = concat $secrets .Values.global.imagePullSecrets }}
{{- end }}
{{- if .Values.image.pullSecrets }}
{{- $secrets = concat $secrets .Values.image.pullSecrets }}
{{- end }}
{{- if $secrets }}
imagePullSecrets:
{{- range $secrets }}
  - name: {{ . }}
{{- end }}
{{- end }}
{{- end -}}

{{/*
Generate environment-specific configuration
*/}}
{{- define "trading-sentinel.environmentConfig" -}}
{{- $environment := .Values.app.environment -}}
{{- $config := dict }}
{{- if eq $environment "development" }}
{{- $config = .Values.development }}
{{- else if eq $environment "staging" }}
{{- $config = .Values.staging }}
{{- else if eq $environment "production" }}
{{- $config = .Values.production }}
{{- end }}
{{- toYaml $config }}
{{- end -}}