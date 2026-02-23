import React, { useEffect, useRef } from 'react';
import { createChart, ColorType } from 'lightweight-charts';

export function TradingChart({ data = [], markers = [], lines = [], height = 500 }) {
    const chartContainerRef = useRef();
    const chartRef = useRef(null);

    useEffect(() => {
        if (!chartContainerRef.current) return;

        // Clean up previous chart
        if (chartRef.current) {
            chartRef.current.remove();
        }

        const chart = createChart(chartContainerRef.current, {
            layout: {
                background: { type: ColorType.Solid, color: '#161a25' },
                textColor: '#d1d4dc',
            },
            grid: {
                vertLines: { color: 'rgba(42, 46, 57, 0.2)' },
                horzLines: { color: 'rgba(42, 46, 57, 0.2)' },
            },
            width: chartContainerRef.current.clientWidth,
            height: height,
            timeScale: {
                timeVisible: true,
                secondsVisible: false,
                borderColor: '#2B2B43',
            },
            rightPriceScale: {
                borderColor: '#2B2B43',
            },
        });

        chartRef.current = chart;

        const candlestickSeries = chart.addCandlestickSeries({
            upColor: '#26a69a',
            downColor: '#ef5350',
            borderVisible: false,
            wickUpColor: '#26a69a',
            wickDownColor: '#ef5350',
        });

        if (data && data.length > 0) {
            candlestickSeries.setData(data);
        }

        // Add Markers
        if (markers && markers.length > 0) {
            candlestickSeries.setMarkers(markers);
        }

        // Add Lines
        if (lines && lines.length > 0) {
            lines.forEach(line => {
                if (line.type === 'price') {
                    candlestickSeries.createPriceLine({
                        price: line.price,
                        color: line.color,
                        lineWidth: 1,
                        lineStyle: 1, // Dotted
                        axisLabelVisible: true,
                        title: line.title,
                    });
                } else if (line.type === 'series') {
                    const lineSeries = chart.addLineSeries({
                        color: line.color || '#4A9EFF',
                        lineWidth: line.lineWidth || 2,
                        lineStyle: 0, // Solid
                        lastValueVisible: false,
                        priceLineVisible: false,
                    });
                    lineSeries.setData(line.data);
                }
            });
        }

        chart.timeScale().fitContent();

        const handleResize = () => {
            if (chartContainerRef.current && chartRef.current) {
                chartRef.current.applyOptions({ width: chartContainerRef.current.clientWidth });
            }
        };

        window.addEventListener('resize', handleResize);

        return () => {
            window.removeEventListener('resize', handleResize);
            if (chartRef.current) {
                chartRef.current.remove();
                chartRef.current = null;
            }
        };
    }, [data, markers, lines, height]); // Re-create chart if data changes (simple approach)

    return (
        <div ref={chartContainerRef} className="w-full relative" style={{ height: height }} />
    );
}
