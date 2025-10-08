"use client"

import { BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from "recharts"

export interface BarChartProps {
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
  stacked?: boolean
}

const defaultColors = [
  "hsl(var(--primary))",     // Sinergy Teal
  "hsl(var(--secondary))",   // Federal Navy
  "#72edef",                 // Teal 300
  "#83a8c3",                 // Navy 400
  "#34e1e6",                 // Teal 400
  "#698eab",                 // Navy 500
]

export function BarChart({
  data,
  dataKeys,
  xAxisKey,
  height = 350,
  showGrid = true,
  showLegend = true,
  showTooltip = true,
  stacked = false,
}: BarChartProps) {
  return (
    <ResponsiveContainer width="100%" height={height}>
      <RechartsBarChart
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
          <Bar
            key={item.key}
            dataKey={item.key}
            name={item.name || item.key}
            fill={item.color || defaultColors[index % defaultColors.length]}
            stackId={stacked ? "stack" : undefined}
            radius={[4, 4, 0, 0]}
          />
        ))}
      </RechartsBarChart>
    </ResponsiveContainer>
  )
}
