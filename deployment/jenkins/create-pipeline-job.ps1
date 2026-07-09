param(
  [string]$JenkinsUrl = "http://localhost:8080",
  [string]$Username = "admin",
  [Parameter(Mandatory = $true)]
  [string]$ApiToken,
  [string]$JobName = "makan-society-deploy",
  [string]$RepoUrl = "https://github.com/pulok529/Makan_Society_ReactPython.git",
  [string]$BranchSpec = "*/main",
  [string]$ScriptPath = "Jenkinsfile",
  [string]$PollSchedule = "H/2 * * * *",
  [switch]$DisablePollScm,
  [switch]$TriggerBuild
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Get-BasicAuthHeader {
  param(
    [string]$User,
    [string]$Token
  )

  $pair = "{0}:{1}" -f $User, $Token
  $bytes = [System.Text.Encoding]::ASCII.GetBytes($pair)
  return "Basic {0}" -f [Convert]::ToBase64String($bytes)
}

function Get-JenkinsCrumb {
  param(
    [string]$BaseUrl,
    [hashtable]$Headers
  )

  try {
    $crumb = Invoke-RestMethod -Method Get -Uri "$BaseUrl/crumbIssuer/api/json" -Headers $Headers
    if ($crumb.crumbRequestField -and $crumb.crumb) {
      return @{
        $crumb.crumbRequestField = $crumb.crumb
      }
    }
  } catch {
    Write-Host "Crumb issuer not available or not required. Continuing without crumb."
  }

  return @{}
}

function New-PipelineJobConfigXml {
  param(
    [string]$RepositoryUrl,
    [string]$Branch,
    [string]$JenkinsfilePath,
    [string]$Schedule,
    [bool]$EnablePollScm
  )

  $escapedRepo = [System.Security.SecurityElement]::Escape($RepositoryUrl)
  $escapedBranch = [System.Security.SecurityElement]::Escape($Branch)
  $escapedScriptPath = [System.Security.SecurityElement]::Escape($JenkinsfilePath)
  $escapedSchedule = [System.Security.SecurityElement]::Escape($Schedule)

  $triggersXml = if ($EnablePollScm) {
@"
  <triggers>
    <hudson.triggers.SCMTrigger>
      <spec>$escapedSchedule</spec>
      <ignorePostCommitHooks>false</ignorePostCommitHooks>
    </hudson.triggers.SCMTrigger>
  </triggers>
"@
  } else {
@"
  <triggers/>
"@
  }

@"
<?xml version='1.1' encoding='UTF-8'?>
<flow-definition plugin="workflow-job">
  <actions/>
  <description>Pipeline job for Makan Society deployment.</description>
  <keepDependencies>false</keepDependencies>
$triggersXml
  <disabled>false</disabled>
  <definition class="org.jenkinsci.plugins.workflow.cps.CpsScmFlowDefinition" plugin="workflow-cps">
    <scm class="hudson.plugins.git.GitSCM" plugin="git">
      <configVersion>2</configVersion>
      <userRemoteConfigs>
        <hudson.plugins.git.UserRemoteConfig>
          <url>$escapedRepo</url>
        </hudson.plugins.git.UserRemoteConfig>
      </userRemoteConfigs>
      <branches>
        <hudson.plugins.git.BranchSpec>
          <name>$escapedBranch</name>
        </hudson.plugins.git.BranchSpec>
      </branches>
      <doGenerateSubmoduleConfigurations>false</doGenerateSubmoduleConfigurations>
      <submoduleCfg class="empty-list"/>
      <extensions/>
    </scm>
    <scriptPath>$escapedScriptPath</scriptPath>
    <lightweight>true</lightweight>
  </definition>
  <properties>
    <org.jenkinsci.plugins.workflow.job.properties.DisableConcurrentBuildsJobProperty/>
  </properties>
</flow-definition>
"@
}

$jenkinsBase = $JenkinsUrl.TrimEnd("/")
$authHeader = Get-BasicAuthHeader -User $Username -Token $ApiToken
$headers = @{
  Authorization = $authHeader
}

$crumbHeaders = Get-JenkinsCrumb -BaseUrl $jenkinsBase -Headers $headers
foreach ($key in $crumbHeaders.Keys) {
  $headers[$key] = $crumbHeaders[$key]
}

$jobConfigXml = New-PipelineJobConfigXml `
  -RepositoryUrl $RepoUrl `
  -Branch $BranchSpec `
  -JenkinsfilePath $ScriptPath `
  -Schedule $PollSchedule `
  -EnablePollScm (-not $DisablePollScm.IsPresent)

$jobCheckUrl = "$jenkinsBase/job/$JobName/api/json"
$jobExists = $false

try {
  Invoke-RestMethod -Method Get -Uri $jobCheckUrl -Headers $headers | Out-Null
  $jobExists = $true
} catch {
  $jobExists = $false
}

if ($jobExists) {
  Write-Host "Updating Jenkins job '$JobName'..."
  Invoke-RestMethod `
    -Method Post `
    -Uri "$jenkinsBase/job/$JobName/config.xml" `
    -Headers $headers `
    -ContentType "application/xml" `
    -Body $jobConfigXml | Out-Null
  Write-Host "Job updated."
} else {
  Write-Host "Creating Jenkins job '$JobName'..."
  Invoke-RestMethod `
    -Method Post `
    -Uri "$jenkinsBase/createItem?name=$([uri]::EscapeDataString($JobName))" `
    -Headers $headers `
    -ContentType "application/xml" `
    -Body $jobConfigXml | Out-Null
  Write-Host "Job created."
}

if ($TriggerBuild.IsPresent) {
  Write-Host "Triggering build for '$JobName'..."
  Invoke-RestMethod -Method Post -Uri "$jenkinsBase/job/$JobName/build" -Headers $headers | Out-Null
  Write-Host "Build triggered."
}

Write-Host ""
Write-Host "Done."
Write-Host "Jenkins URL : $jenkinsBase"
Write-Host "Job Name    : $JobName"
Write-Host "Repo URL    : $RepoUrl"
Write-Host "Branch      : $BranchSpec"
Write-Host "Script Path : $ScriptPath"
Write-Host "Poll SCM    : $([bool](-not $DisablePollScm.IsPresent))"
if (-not $DisablePollScm.IsPresent) {
  Write-Host "Schedule    : $PollSchedule"
}
