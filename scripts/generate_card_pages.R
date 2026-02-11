red_cards <- readr::read_csv2("generate_cards/CardContentRed.csv")
white_cards <- readr::read_csv2("generate_cards/CardContentWhite.csv")

anchors <- stringi::stri_extract(red_cards$Link, regex = "(?=#).*")

cards <- glue::glue_data(
  red_cards,
  .open = "[",
  .close = "]",
  "
  ## [Text] {[anchors]}

  [Quote]

  <[ExtLink]>

  "
)

writeLines(sprintf("# Red Cards\n\n%s", paste0(cards, collapse = "\n")), "cards.qmd")
writeLines(sprintf("# White Cards\n\n%s", paste0("- ", white_cards$Text, collapse = "\n")), "white-cards.qmd")
