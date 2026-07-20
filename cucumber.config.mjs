export default {
  paths: ["tests/cucumber/**/*.feature"],
  import: ["tests/cucumber/steps/**/*.mjs"],
  format: ["progress", "json:reports/cucumber.json"],
};
