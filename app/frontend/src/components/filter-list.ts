import { defineComponent } from "./define";

function normalize(text: string): string {
  return text
    .toLowerCase()
    .normalize("NFD")
    .replace(/[̀-ͯ]/g, "");
}

/**
 * Filtre instantané d'une liste côté navigateur (catalogue du magasin, films…).
 * Chaque élément porte `data-search="texte"` et `data-tags="tag1 tag2"`.
 */
export const filterList = () =>
  defineComponent({
    query: "",
    tags: [] as string[],
    visibleCount: 0,
    init() {
      this.apply();
    },
    toggleTag(tag: string) {
      this.tags = this.tags.includes(tag) ? this.tags.filter((t) => t !== tag) : [...this.tags, tag];
      this.apply();
    },
    hasTag(tag: string) {
      return this.tags.includes(tag);
    },
    clear() {
      this.query = "";
      this.tags = [];
      this.apply();
    },
    isFiltered() {
      return this.query.trim() !== "" || this.tags.length > 0;
    },
    apply() {
      const words = normalize(this.query).split(/\s+/).filter(Boolean);
      let count = 0;
      this.$el.querySelectorAll<HTMLElement>("[data-search]").forEach((item) => {
        const haystack = normalize(item.dataset.search ?? "");
        const itemTags = (item.dataset.tags ?? "").split(" ");
        const matchesText = words.every((word) => haystack.includes(word));
        const matchesTags = this.tags.length === 0 || this.tags.some((tag) => itemTags.includes(tag));
        const visible = matchesText && matchesTags;
        item.hidden = !visible;
        if (visible) count += 1;
      });
      this.visibleCount = count;
    },
  });
