let pageData = JSON.parse(document.getElementById('pageData').textContent);

const HistoryRendering = {
  delimiters: ['{', '}'],
  data() {
    return {
        edits: [],
        diffPrevEdit: null,
        diffNextEdit: null,
    }
  },
  methods: {
      setInitial() {
        this.edits = pageData["edits"];
      },
      getLastEdit(edit) {
        return this.edits.filter(ed => ed["section"] == edit["section"]).find(ed => new Date(ed["created_date"]) < new Date(edit["created_date"]));
      },
      isLatestEdit(edit) {
        let nextEdit = this.edits.filter(ed => ed["section"] == edit["section"]).find(ed => new Date(ed["created_date"]) > new Date(edit["created_date"]));
        return nextEdit == null;
      },
      getEditDiff(edit) {
        let previousSecEdit = this.getLastEdit(edit);
        if (previousSecEdit != null) {
            let diff = edit["num_words"] - previousSecEdit["num_words"];
            let diffChar = diff >= 0 ? "+" : "";
            return diffChar + diff;
        } else {
            return "+" + edit["num_words"];
        }
      },
      getEditById(editId) {
        return this.edits.find(ed => ed["id"] === parseInt(editId));
      },
      viewEditDiff(event) {
        let editId = event.target.attributes['data-edit-id'].value;
        this.diffNextEdit = this.getEditById(editId);
        this.diffPrevEdit = this.getLastEdit(this.diffNextEdit);
      },
      getEditDiffHeader(edit) {
        return  edit['writer_username'] + " on " + new Date(edit['created_date']).toLocaleString();
      }
  }

}

const app = Vue.createApp(HistoryRendering);
const mountedApp = app.mount('#vue-app');
mountedApp.setInitial();
