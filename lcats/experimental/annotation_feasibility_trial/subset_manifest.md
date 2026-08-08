# Annotation feasibility trial: subset manifest

24 stories (3 per genre x 8 `VALID_GENRES`), selected by hand from
`corpora/` -- title/author/opening-text judgment only, no paid API
call -- for `WI-ANNOTATE-0054`'s feasibility run. `provisional_genre`
is this manual guess, to compare against `lcats annotate`'s actual
`detected_genre` output in the stats report.

| source (corpora/) | provisional_genre | rationale | body_chars |
|---|---|---|---|
| mass_quantities/a_martian_odyssey__weinbaum | science fiction | Classic pulp SF; Mars exploration, alien contact (Weinbaum). | 56753 |
| mass_quantities/2_b_r_0_2_b__vonnegut | science fiction | Vonnegut dystopian-future SF (population control, euthanasia). | 14409 |
| mass_quantities/a_city_near_centaurus__doede | science fiction | Title signals interstellar/space setting. | 28026 |
| lovecraft/the_call_of_cthulhu | horror | Lovecraft; cosmic horror, canonical genre example. | 70070 |
| lovecraft/the_dunwich_horror | horror | Lovecraft; supernatural threat, title says horror. | 100961 |
| lovecraft/the_colour_out_of_space | horror | Lovecraft; dread/alien contamination horror. | 69283 |
| wodehouse/extricating_young_gussie | humor | Wodehouse; farcical comedy of manners. | 43257 |
| wodehouse/crowned_heads | humor | Wodehouse; comedic tone throughout the collection. | 33333 |
| wodehouse/one_touch_of_nature | humor | Wodehouse; comedic tone throughout the collection. | 25217 |
| grimm/rapunzel | fantasy | Fairy tale; magic, witch, tower -- fantasy elements. | 7920 |
| grimm/hansel_and_gretel | fantasy | Fairy tale; witch, magic forest -- fantasy elements. | 16775 |
| grimm/snow_white_and_rose_red | fantasy | Fairy tale; enchanted bear/dwarf -- fantasy elements. | 13988 |
| sherlock/scandal_in_bohemia | mystery | Sherlock Holmes; detective mystery, canonical genre example. | 46611 |
| sherlock/red_headed_league | mystery | Sherlock Holmes; detective mystery. | 49419 |
| sherlock/speckled_band | mystery | Sherlock Holmes; detective mystery. | 53158 |
| london/love_of_life | adventure | Jack London; wilderness survival adventure. | 44068 |
| london/story_of_keesh | adventure | Jack London; Arctic/hunting adventure. | 16782 |
| london/brown_wolf | adventure | Jack London; wilderness setting, man-vs-nature adventure. | 31817 |
| mass_quantities/the_sheriff_and_his_partner__harris | western | Opens in frontier Kansas, 1869; sheriff protagonist. | 39377 |
| mass_quantities/the_cowboy_and_the_lady_and_her_pa_b_a_story_of_a__cobb | western | Wagon-train boss, cowboy protagonist, frontier setting. | 41789 |
| ohenry-whirligigs/chaparral_christmas_gift | western | O. Henry 'Heart of the West' story; Texas ranch/prairie setting. | 10517 |
| ohenry-four_million/gift_of_the_magi | romance | O. Henry; canonical romantic-sacrifice story. | 11259 |
| ohenry-four_million/springtime_a_la_carte | romance | O. Henry; romantic-comedy premise (personal ad courtship). | 12435 |
| ohenry-four_million/service_of_love | romance | O. Henry; title and premise center on a marriage/romance. | 11518 |
