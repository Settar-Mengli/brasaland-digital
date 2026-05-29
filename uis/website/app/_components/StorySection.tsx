export default function StorySection() {
  return (
    <section
      id="story"
      aria-labelledby="story-heading"
      className="bg-brasaland-ivory py-20 sm:py-24"
    >
      <div className="max-w-4xl mx-auto px-4 sm:px-6 text-center">
        <p className="font-sans text-sm font-semibold tracking-widest uppercase text-brasaland-ember">
          Since 2008
        </p>
        <h2
          id="story-heading"
          className="mt-3 font-display text-3xl sm:text-4xl font-bold text-brasaland-charcoal"
        >
          Our Story
        </h2>
        <p className="mt-6 text-lg text-brasaland-charcoal/80 leading-relaxed">
          Founded in Medellín in 2008, Brasaland began as a family dream — sharing the authentic
          taste of grilled meat with consistent quality and warm service. Today we are 14
          restaurants across two countries, but we maintain the same recipe for success: fresh
          ingredients, traditional techniques, and a passion for every dish we serve.
        </p>
      </div>
    </section>
  );
}
