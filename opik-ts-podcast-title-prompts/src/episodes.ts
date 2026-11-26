export interface Episode {
  show: string;
  notes: string;
  guest?: string;
}

// Fictional episodes for the invented "Foxglove Audio" network.
export const EPISODES: Episode[] = [
  {
    show: "Tidewater Tales",
    guest: "Marisol Okafor",
    notes:
      "Marisol Okafor, a harbor pilot in Savannah, explains how she guides 300-metre container ships through a channel only 120 metres wide, and what happens when the fog rolls in.",
  },
  {
    show: "The Spreadsheet Hour",
    notes:
      "We rebuild a household budget from scratch using only three formulas. Hosts argue about whether VLOOKUP deserves its retirement.",
  },
  {
    show: "Night Shift Radio",
    guest: "Dev Pillai",
    notes:
      "Dev Pillai has repaired church organs for 31 years. He talks about a 1902 instrument with 2,400 pipes and the mouse nest he found inside the bellows.",
  },
  {
    show: "Small Town Science",
    notes:
      "A middle-school class in Duluth measures how fast a snowbank melts. The episode follows their data, their disagreements, and their surprisingly accurate final graph.",
  },
  {
    show: "Tidewater Tales",
    guest: "Anneliese Brandt",
    notes:
      "Anneliese Brandt restores wooden sailboats in a Maine boatyard. This week: replacing a cracked keel on a 1958 sloop and why she refuses to use fiberglass.",
  },
  {
    show: "The Spreadsheet Hour",
    guest: "Tomasz Weil",
    notes:
      "Tomasz Weil, an accountant for a touring circus, shows how he tracks hay, tent repairs, and elephant insurance in one shared workbook.",
  },
];
