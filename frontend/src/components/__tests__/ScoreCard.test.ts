import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import { defineComponent, h } from "vue";
import ScoreCard from "../ScoreCard.vue";
import type { EvaluationResult } from "../../api/evaluations";

const mockEvaluation: EvaluationResult = {
  id: 1,
  test_run_id: 1,
  judge_type: "llm",
  overall_score: 4.2,
  accuracy_score: 5,
  hallucination_score: 4,
  tool_correctness_score: 3,
  expression_quality_score: 4,
  judge_reasoning: "回答准确，整体质量良好。",
  rule_results: null,
  created_at: "2026-01-01T00:00:00Z",
};

const NCardStub = defineComponent({
  props: ["title"],
  setup(props, { slots }) {
    return () =>
      h("div", [
        h("div", { class: "card-title" }, props.title),
        slots.default ? slots.default() : null,
      ]);
  },
});

const NAlertStub = defineComponent({
  setup(_, { slots }) {
    return () =>
      h("div", [
        slots.header ? h("div", { class: "alert-header" }, slots.header()) : null,
        slots.default ? slots.default() : null,
      ]);
  },
});

const stubs = {
  NCard: NCardStub,
  NSpace: { template: "<div><slot /></div>" },
  NText: { template: "<span><slot /></span>" },
  NProgress: { template: "<div></div>" },
  NAlert: NAlertStub,
};

describe("ScoreCard", () => {
  it("displays overall score", () => {
    const wrapper = mount(ScoreCard, {
      props: { evaluation: mockEvaluation },
      global: { stubs },
    });
    expect(wrapper.text()).toContain("4.2");
  });

  it("displays dimension scores", () => {
    const wrapper = mount(ScoreCard, {
      props: { evaluation: mockEvaluation },
      global: { stubs },
    });
    expect(wrapper.text()).toContain("准确性");
    expect(wrapper.text()).toContain("无幻觉");
    expect(wrapper.text()).toContain("工具调用正确性");
    expect(wrapper.text()).toContain("表达质量");
  });

  it("displays judge reasoning", () => {
    const wrapper = mount(ScoreCard, {
      props: { evaluation: mockEvaluation },
      global: { stubs },
    });
    expect(wrapper.text()).toContain("回答准确");
  });

  it("shows rule judge type label", () => {
    const ruleEval: EvaluationResult = {
      ...mockEvaluation,
      judge_type: "rule",
      overall_score: 5.0,
      accuracy_score: null,
      hallucination_score: null,
      tool_correctness_score: null,
      expression_quality_score: null,
    };
    const wrapper = mount(ScoreCard, {
      props: { evaluation: ruleEval },
      global: { stubs },
    });
    expect(wrapper.text()).toContain("规则评分");
    expect(wrapper.text()).toContain("5.0");
  });
});
