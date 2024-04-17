# Check URLs for link rot
library(tibble)
library(dplyr)
library(stringr)
library(gh)
library(glue)

link_file <- "cards.qmd"

qmd_file <- readLines(link_file)

cards <- na.omit(stringr::str_extract(qmd_file, "(?<=##\\s).*"))
urls <- na.omit(stringr::str_extract(qmd_file, "(?<=<).*(?=>)"))

links_tbl <- tibble::tibble(card = cards, url = urls)

status <- vector(mode = "numeric", length = nrow(links_tbl))
cli::cli_h1("Checking links")
for(i in 1:nrow(links_tbl)){
  cli::cli_progress_message(paste("Checking status of card", links_tbl$card[i]))
  cli::cli_h2(links_tbl$card[i])
  #print(sprintf("Checking status of card: %s...", links_tbl$card[i]))
  status[i] <- httr::GET(url = links_tbl$url[i])$status_code
  if(status[i] == 200){
    cli::cli_alert_success(status[i])
  } else {
    cli::cli_alert_warning(status[i])
  }
}
links_tbl <- links_tbl |>
  mutate(status_code = status)

rotten_links <- links_tbl |>
  filter(status_code != 200 & status_code != 403) # 403 is related to sites preventing scraping?

if(nrow(rotten_links) == 0) {
  cli::cli_alert_success("All links are working! Just sit back, relax, and enjoy the tens of seconds you have gained from not having to take any action.")
} else {
  gh_token <- Sys.getenv("GITHUB_PAT")
  title <- "Possible rotten link(s) detected"
  body <- glue::glue_data(rotten_links,
    "
    {card}: {url}
    "
  )
  gh(
    "/repos/nlesc/open-loves-science/issues",
    title = title,
    body = body,
    .token = gh_token,
    .method = "POST"
  )
}
