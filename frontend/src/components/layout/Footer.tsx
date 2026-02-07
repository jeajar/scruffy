const quotes = [
  "Scruffy's gonna clean this place up. Mh-hmm.",
  "I've never seen him so proud.",
  "Scruffy's gonna die the way he lived.",
  "Life and death are a seamless continuum.",
  "What fevered dream is this that bids to tear this company in twain?",
  "Scruffy believes in this company.",
  "Second.",
  "Yup.",
  "Mmhmm.",
];

function getRandomQuote() {
  return quotes[Math.floor(Math.random() * quotes.length)];
}

export function Footer() {
  return (
    <footer className="bg-scruffy-dark border-t border-gray-700 mt-auto">
      <div className="mx-auto max-w-7xl px-4 py-4 sm:px-6 lg:px-8">
        <p className="text-center text-sm text-gray-400">
          <em>"{getRandomQuote()}"</em>
          <span className="ml-2">- Scruffy, the Janitor</span>
        </p>
      </div>
    </footer>
  );
}
