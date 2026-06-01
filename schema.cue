package helia

import "list"

#Service: "TELEPHONIE_FIXE" | "TELEPHONIE_MOBILE" | "INTERNET_FIXE" |
          "INTERNET_MOBILE" | "FIBRE_OPTIQUE" | "RESEAU_CUIVRE" |
          "LIAISONS_CELERIS_ETHERNET"

#Impact: "COUPURE_20_30_MIN" | "COUPURE_30_MIN" | "A_DETERMINER"

#Maintenance: {
    id:                        =~"^[0-9a-f]{8}$"
    scraped_at:                string
    source_url:                string
    timestamp_debut:           string
    timestamp_fin:             string
    duree_fenetre_minutes:     >0
    duree_coupure_min_minutes: int | null
    duree_coupure_max_minutes: int | null
    communes_concernees:       [...string] & list.MinItems(1)
    services:                  [...#Service] & list.MinItems(1)
    impact:                    #Impact
}
