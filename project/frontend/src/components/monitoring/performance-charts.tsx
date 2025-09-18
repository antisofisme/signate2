import React from 'react';

interface PerformanceChartsProps {
  data?: Array<{
    time: string;
    value: number;
  }>;
}

export const PerformanceCharts: React.FC<PerformanceChartsProps> = ({ data = [] }) => {
  return (
    <div className="rounded-lg border p-4">
      <h3 className="font-medium mb-4">Performance Metrics</h3>
      <div className="h-64 flex items-center justify-center bg-muted rounded">
        <p className="text-muted-foreground">Chart placeholder - integrate with recharts</p>
      </div>
    </div>
  );
};

export default PerformanceCharts;