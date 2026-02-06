import random
from dataclasses import dataclass


@dataclass(frozen=True)
class ScruffyQuotes:
    """Domain value object holding Scruffy's signature quotes."""

    _quotes: tuple[str, ...] = (
        "Scruffy's gonna die they way he lived. *turns page*",
        "Prisons not so bad. You can make sangria in the terlet. Course it's shank or be shanked.",
        "Life and death are a seamless continuum. Mh-hmm.",
        "Scruffy votes his 40,000 shares for the mysterious stranger",
        "Scruffy believes in this company. *sniff*",
        "It's wrong, wash bucket. Oh, it would be sweet for a while, but in the back of our minds we'd know that I'm a man, and you're janitorial equipment.",
        "Second.",
        "Mmm hmm.",
        "Scruffy's gonna get himself one of them $300 haircuts. This one's lost its pizzazz.",
        "A greater tragedy my eyes have never beheld. Welp, into the turlet.",
        "My job? Toilets 'n boilers, boilers 'n toilets, plus that one boilin' toilet. Fire me if'n you dare.",
    )

    def random(self) -> str:
        """Return a random Scruffy quote."""
        return random.choice(self._quotes)


# Default instance for convenience
SCRUFFY_QUOTES = ScruffyQuotes()
