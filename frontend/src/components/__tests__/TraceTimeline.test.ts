import { describe, it, expect } from "vitest";
import { mount } from "@vue/test-utils";
import { defineComponent, h } from "vue";
import TraceTimeline from "../TraceTimeline.vue";
import type { RunStep } from "../../api/testRuns";

const mockSteps: RunStep[] = [
  {
    id: 1,
    sequence: 1,
    step_type: "intent_detection",
    name: "IntentDetector",
    input_json: { query: "test" },
    output_json: { intent: "search" },
    latency_ms: 100,
    token_usage_input: 10,
    token_usage_output: 20,
    status: "success",
    error_message: null,
  },
  {
    id: 2,
    sequence: 2,
    step_type: "llm_generation",
    name: "LLMCall",
    input_json: {},
    output_json: {},
    latency_ms: 2000,
    token_usage_input: 50,
    token_usage_output: 100,
    status: "success",
    error_message: null,
  },
];

const NTimelineItemStub = defineComponent({
  props: ["title"],
  setup(props, { slots }) {
    return () =>
      h("div", [
        h("div", { class: "title" }, props.title),
        slots.content ? slots.content() : slots.default ? slots.default() : null,
      ]);
  },
});

const NCollapseItemStub = defineComponent({
  props: ["title"],
  setup(props, { slots }) {
    return () =>
      h("div", [
        h("div", { class: "collapse-title" }, props.title),
        slots.default ? slots.default() : null,
      ]);
  },
});

const stubs = {
  NTimeline: { template: "<div><slot /></div>" },
  NTimelineItem: NTimelineItemStub,
  NTag: { template: "<span><slot /></span>" },
  NCollapse: { template: "<div><slot /></div>" },
  NCollapseItem: NCollapseItemStub,
  NSpace: { template: "<div><slot /></div>" },
  NAlert: { template: "<div><slot /></div>" },
};

describe("TraceTimeline", () => {
  it("renders steps in order", () => {
    const wrapper = mount(TraceTimeline, {
      props: { steps: mockSteps },
      global: { stubs },
    });
    expect(wrapper.text()).toContain("IntentDetector");
    expect(wrapper.text()).toContain("LLMCall");
    expect(wrapper.text()).toContain("intent_detection");
    expect(wrapper.text()).toContain("llm_generation");
  });

  it("shows error status for failed steps", () => {
    const errorSteps: RunStep[] = [
      {
        id: 1,
        sequence: 1,
        step_type: "llm_generation",
        name: "LLM",
        input_json: {},
        output_json: {},
        latency_ms: 5000,
        token_usage_input: 0,
        token_usage_output: 0,
        status: "error",
        error_message: "timeout error",
      },
    ];
    const wrapper = mount(TraceTimeline, {
      props: { steps: errorSteps },
      global: { stubs },
    });
    expect(wrapper.text()).toContain("timeout error");
    expect(wrapper.text()).toContain("error");
  });

  it("renders empty steps array without error", () => {
    const wrapper = mount(TraceTimeline, {
      props: { steps: [] },
      global: { stubs },
    });
    expect(wrapper.exists()).toBe(true);
  });

  it("shows latency and token info", () => {
    const wrapper = mount(TraceTimeline, {
      props: { steps: mockSteps },
      global: { stubs },
    });
    expect(wrapper.text()).toContain("100ms");
    expect(wrapper.text()).toContain("2000ms");
  });
});
