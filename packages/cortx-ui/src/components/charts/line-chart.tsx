"use client"

import { LineChart as RechartsLineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

export interface LineChartProps {
  data: any[]
  dataKeys: {
    key: string
    name?: string
    color?: string
  }[]
  xAxisKey: string
  height?: number
  showGrid?: boolean
  showLegend?: boolean
  showTooltip?: boolean
}

const defaultColors = [
  "hsl(var(--primary))",     // Sinergy Teal
  "hsl(var(--secondary))",   // Federal Navy
  "#72edef",                 // Teal 300
  "#83a8c3",                 // Navy 400
  "#34e1e6",                 // Teal 400
  "#698eab",                 // Navy 500
]

export function LineChart({
  data,
  dataKeys,
  xAxisKey,
  height = 350,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
}: LineChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsLineChart
        data={data}
        margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
      >
        {showGrid && <CartesianGrid strokeDasharray="3 3" className="stroke-muted" />}
        <XAxis
          dataKey={xAxisKey}
          className="text-xs text-muted-foreground"
          tick={{ fill: "hsl(var(--muted-foreground))" }}
        />
        <YAxis
          className="text-xs text-muted-foreground"
          tick={{ fill: "hsl(var(--muted-foreground))" }}
        />
        {showTooltip && (
          <Tooltip
            contentStyle={{
              backgroundColor: "hsl(var(--popover))",
              border: "1px solid hsl(var(--border))",
              borderRadius: "var(--radius)",
              color: "hsl(var(--popover-foreground))",
            }}
          />
        )}
        {showLegend && <Legend />}
        {dataKeys.map((item, index) => (
          <Line
            key={item.key}
            type="monotone"
            dataKey={item.key}
            name={item.name || item.key}
            stroke={item.color || defaultColors[index % defaultColors.length]}
            strokeWidth={2}
            dot={{ fill: item.color || defaultColors[index % defaultColors.length] }}
            activeDot={{ r: 6 }}
          />
        ))}
      </RechartsLineChart>
    </ResponsiveContainer>
  )
}
