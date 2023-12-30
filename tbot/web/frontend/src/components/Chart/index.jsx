import { createChart, ColorType } from 'lightweight-charts';
import React, { useEffect, useRef, useState } from 'react';

import {getApiURL} from '/src/util/api'

const backgroundColor ='black'
const lineColor = '#2962FF'
const textColor = 'white'
const areaTopColor = '#2962FF'
const areaBottomColor = 'rgba(41, 98, 255, 0.28)'

export default class Chart extends React.Component {
  state = {
    symbol: "/ES=F",
    timeframe: '5m',
    chart: null,
  }

  constructor(props) {
    super(props);
    this.containerChartRef = React.createRef(null);
  }

  componentDidMount() {
    this.updateChartData()
  }

  componentWillUnmount() {
    if (this.state.chart) {
      this.state.chart.remove();
    }
  }

  updateChartData = () => {
    fetch(`${getApiURL()}/api/trade`, {
      method: "post",
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        symbol: this.state.symbol,
        timeframe: this.state.timeframe
      })
    })
    .then(response => response.json())
    .then(data => {
      this.loadChart(data)
    })
  }

  onButtonUpdate = (event) => {
    this.updateChartData()
  }

	loadChart = (data) => {
    if (this.state.chart) {
      this.state.chart.remove();
    }

    // Create a chart
    const chart = createChart(this.containerChartRef.current, {
      layout: {
        background: { type: ColorType.Solid, color: backgroundColor },
        textColor
      },
      timeScale: {
        timeVisible: true
      },
      grid: {
        horzLines: {
          color: 'grey'
        },
        vertLines: {
          color: 'grey'
        }
      }
    });
    chart.timeScale().fitContent();

    // Add candles
    const series = chart.addCandlestickSeries({
      upColor: '#26a69a', downColor: '#ef5350', borderVisible: false,
      wickUpColor: '#26a69a', wickDownColor: '#ef5350',
    });
    series.setData(data["candles"]);

    // Add horizontal support and resistance
    for (let i = 0; i < data["s_r"].length; i++) {
      series.createPriceLine({
        price: data["s_r"][i],
        color: '#bf00ff',
        lineWidth: 2,
        //lineStyle: 0,
        axisLabelVisible: false
      });
    }

    series.setData(data["candles"]);
    chart.timeScale().fitContent();

    // Save the chart
    this.setState({chart: chart})
	}

  render() {
    return (
      <main className="flex flew-row">
        <div
            className="flex w-5/6 min-h-screen"
            ref={this.containerChartRef}
          />
        <div className="w-1/6 flex flex-col items-center m-8">
          <h1 className="text-2xl p-8"> Select Symbol </h1>
          <div className="flex flex-row m-4">

            <select name="symbols" id="symbols" defaultValue={this.state.symbol} onChange={e => this.setState({symbol: e.target.value})}
              className="mx-2 px-2 rounded-md">
              <option value="/ES=F">/ES=F</option>
              <option value="/BTC=F">/BTC=F</option>
              <option value="/NQ=F">/NQ=F</option>
              <option value="/CL=F">/CL=F</option>
              <option value="TSLA">TSLA</option>
            </select>

            <select name="times" id="times" defaultValue={this.state.timeframe} onChange={e => this.setState({timeframe: e.target.value})}
              className="mx-2 px-2 rounded-md">
              <option value="1m">1m</option>
              <option value="5m">5m</option>
              <option value="15m">15m</option>
              <option value="1h">1h</option>
              <option value="1d">D</option>
              <option value="1wk">W</option>
            </select>

            <button
              onClick={(e) => this.onButtonUpdate()}
              className="mx-2 px-4 py-2 rounded-md bg-white hover:bg-teal-500 hover:text-white active:bg-teal-700">
                Update
            </button>
          </div>
        </div>
      </main>

    );
  }
};
