import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description: "Evaluate an arithmetic expression exactly.",
  args: {
    expression: tool.schema.string().describe("The expression, e.g. 1234567 * 7654321"),
  },
  async execute(args, context) {
    const script = path.join(context.worktree, ".opencode/tools/calc.py")
    const result = await Bun.$`python3 ${script} ${args.expression}`.text()
    return result.trim()
  },
})
