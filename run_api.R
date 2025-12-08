# DIMSpec API 서버 시작 스크립트
# 이 스크립트를 실행하면 API 서버가 백그라운드에서 시작됩니다

# 필요한 소스 파일 로드
source(here::here("config", "env_glob.txt"))
source(here::here("config", "env_R.R"))
source(here::here("R", "app_functions.R"))
source(here::here("R", "db_comm.R"))

# API 서버 시작
cat("API 서버를 시작합니다...\n")
start_api(background = TRUE)

cat("\nAPI 서버가 백그라운드에서 실행 중입니다.\n")
cat("Shiny 앱을 실행하려면:\n")
cat("  library(shiny)\n")
cat("  runApp('inst/apps/msmatch')\n\n")
cat("API 서버를 중지하려면:\n")
cat("  api_stop()\n")
