// Reference solution, exercise 2, task 4: goes into .opencode/tools/ next to data_summary.py
import { tool } from "@opencode-ai/plugin"
import path from "path"

export default tool({
  description:
    "Summarise a CSV file of station data: number of rows, date range, and for each column the missing values (-999, with their dates) and the range of the valid values. Use this to get an overview of a data file instead of reading it.",
  args: {
    file: tool.schema.string().describe("Path of the CSV file relative to the project root, e.g. data/munich_daily.csv"),
  },
  async execute(args, context) {
    const script = path.join(context.worktree, ".opencode/tools/data_summary.py")
    const result = await Bun.$`python3 ${script} ${path.join(context.worktree, args.file)}`.text()
    return result.trim()
  },
})
