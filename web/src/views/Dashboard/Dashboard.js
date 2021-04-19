import React, { Component } from 'react';
import classes from "./Dashboard.module.css";
import LineGraph from "../../components/Dashboard/LineGraph";
import chartIcon from "../../assets/chart-icon.svg";
import { managerData, nationalAverageData, yearLabels, managerQuarterData, nationalAverageQuarterData, quarterLabels } from "../../mockData";

export default class Dashboard extends Component {
    state = {
        data: managerData,
        average: nationalAverageData,
        labels: yearLabels
    }

    handleButtonClick = e => {
        const { value } = e.target;
        const isAnnual = value === "annual";

        const newData = isAnnual ? managerData : managerQuarterData;
        const newLabels = isAnnual ? yearLabels : quarterLabels;
        const newAverage = isAnnual ? nationalAverageData : nationalAverageQuarterData;

        this.setState({
            data: newData,
            average: newAverage,
            labels: newLabels
        })
    }

    render() {
        const { data, average, labels } = this.state;
        return (
            <div className={classes.container}>
                <header>
                    <img src={chartIcon} alt="bar chart icon" />
                    <h1>Strategy Performance</h1>
                </header>

                <div className={classes.buttonContainer}>
                    <button className={classes.buttonFirst}
                        value="annual"
                        onClick={this.handleButtonClick}
                    >
                        10 Year
                    </button>

                    <button
                        value="lastquarter"
                        onClick={this.handleButtonClick}
                    >
                        1 Year
                    </button>

                    <button className={classes.buttonLast}
                        value="lastquarter"
                        onClick={this.handleButtonClick}
                    >
                        1 Month
                    </button>
                </div>

                <LineGraph
                    data={data}
                    average={average}
                    labels={labels} />

            </div>
        )
    }
}
