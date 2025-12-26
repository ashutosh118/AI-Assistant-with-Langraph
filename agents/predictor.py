import pandas as pd
import numpy as np
from typing import Dict, Any, List, Union
import streamlit as st
from config.settings import settings
from utils.models import model_manager
from utils.vector_store import vector_store

class PredictionAgent:
    """Agent for making predictions and data analysis"""
    
    def __init__(self):
        self.name = "Prediction Agent"
        self.description = "Makes predictions and performs data analysis"
    
    def analyze_trend(self, data: List[Union[int, float]], labels: List[str] = None) -> Dict[str, Any]:
        """Analyze trend in numerical data"""
        try:
            if len(data) < 2:
                return {"error": "Insufficient data points for trend analysis"}
            
            # Convert to numpy array
            y = np.array(data, dtype=float)
            x = np.arange(len(y))
            
            # Calculate trend using linear regression
            slope, intercept = np.polyfit(x, y, 1)
            
            # Calculate correlation coefficient
            correlation = np.corrcoef(x, y)[0, 1]
            
            # Determine trend direction
            if slope > 0.1:
                trend_direction = "Increasing"
            elif slope < -0.1:
                trend_direction = "Decreasing"
            else:
                trend_direction = "Stable"
            
            # Calculate predictions for next few points
            next_points = 3
            future_x = np.arange(len(y), len(y) + next_points)
            predictions = slope * future_x + intercept
            
            analysis = {
                "trend_direction": trend_direction,
                "slope": slope,
                "correlation": correlation,
                "strength": "Strong" if abs(correlation) > 0.7 else "Moderate" if abs(correlation) > 0.4 else "Weak",
                "predictions": predictions.tolist(),
                "data_points": len(data),
                "mean": np.mean(y),
                "std_dev": np.std(y)
            }
            
            return analysis
            
        except Exception as e:
            return {"error": f"Error in trend analysis: {e}"}
    
    def simple_forecast(self, data: List[Union[int, float]], periods: int = 3) -> Dict[str, Any]:
        """Simple forecasting using moving average and trend"""
        try:
            if len(data) < 3:
                return {"error": "Insufficient data for forecasting"}
            
            # Convert to numpy array
            y = np.array(data, dtype=float)
            
            # Calculate moving average (last 3 points)
            window_size = min(3, len(y))
            moving_avg = np.mean(y[-window_size:])
            
            # Calculate trend from last few points
            if len(y) >= 2:
                recent_trend = y[-1] - y[-2]
            else:
                recent_trend = 0
            
            # Generate forecasts
            forecasts = []
            last_value = y[-1]
            
            for i in range(periods):
                # Simple forecast: last value + trend + some smoothing
                forecast = last_value + recent_trend * (i + 1) * 0.8  # Dampen trend
                forecasts.append(forecast)
            
            # Calculate confidence intervals (simple approach)
            std_dev = np.std(y)
            confidence_intervals = [
                (forecast - 1.96 * std_dev, forecast + 1.96 * std_dev)
                for forecast in forecasts
            ]
            
            return {
                "forecasts": forecasts,
                "confidence_intervals": confidence_intervals,
                "method": "Simple trend + moving average",
                "periods": periods,
                "base_std_dev": std_dev
            }
            
        except Exception as e:
            return {"error": f"Error in forecasting: {e}"}
    
    def analyze_pattern(self, text_data: str) -> str:
        """Analyze patterns in text data"""
        try:
            prompt = f"""Please analyze the following data for patterns, trends, and insights:

{text_data}

Provide analysis on:
1. Key patterns observed
2. Trends or changes over time
3. Notable insights or anomalies
4. Potential predictions or forecasts based on the data
5. Recommendations based on findings

Analysis:"""
            
            analysis = model_manager.azure_llm.invoke(prompt)
            if hasattr(analysis, 'content'):
                analysis = analysis.content
            return analysis
            
        except Exception as e:
            return f"Error analyzing patterns: {e}"
    
    def make_prediction(self, context: str, query: str) -> str:
        """Make predictions based on context and query"""
        try:
            prompt = f"""Based on the following context, please make an informed prediction or analysis for the query: "{query}"

Context:
{context}

Please provide:
1. Your prediction or analysis
2. Reasoning behind the prediction
3. Key factors considered
4. Confidence level and limitations
5. Alternative scenarios if applicable

Prediction:"""
            
            prediction = model_manager.azure_llm.invoke(prompt)
            if hasattr(prediction, 'content'):
                prediction = prediction.content
            return prediction
            
        except Exception as e:
            return f"Error making prediction: {e}"
    
    def process_query(self, query: str, data: Any = None) -> str:
        """Process a prediction query"""
        try:
            query_lower = query.lower()

            # Detect direct data list in query (e.g., [1, 3, 5, 7, 9, 11])
            import re
            data_list_match = re.search(r'\[\s*[-+]?\d+(?:\.\d+)?(?:\s*,\s*[-+]?\d+(?:\.\d+)?)*\s*\]', query)
            if data_list_match:
                # Extract numbers from the list
                numbers = re.findall(r'[-+]?\d+(?:\.\d+)?', data_list_match.group())
                numerical_data = [float(x) for x in numbers]
                if numerical_data and len(numerical_data) >= 2:
                    if "trend" in query_lower or "analyze" in query_lower:
                        analysis = self.analyze_trend(numerical_data)
                        if "error" in analysis:
                            return analysis["error"]
                        result = f"""**Trend Analysis:**
- Direction: {analysis['trend_direction']}
- Strength: {analysis['strength']} (correlation: {analysis['correlation']:.3f})
- Slope: {analysis['slope']:.3f}
- Data Points: {analysis['data_points']}
- Mean: {analysis['mean']:.2f}
- Standard Deviation: {analysis['std_dev']:.2f}

**Predictions for next 3 points:**
{', '.join([f'{pred:.2f}' for pred in analysis['predictions']])}"""
                        return result
                    elif "forecast" in query_lower or "predict" in query_lower:
                        forecast = self.simple_forecast(numerical_data)
                        if "error" in forecast:
                            return forecast["error"]
                        result = f"""**Forecast Results:**
Method: {forecast['method']}
Periods: {forecast['periods']}

**Forecasted Values:**
"""
                        for i, (pred, ci) in enumerate(zip(forecast['forecasts'], forecast['confidence_intervals'])):
                            result += f"Period {i+1}: {pred:.2f} (95% CI: {ci[0]:.2f} - {ci[1]:.2f})\n"
                        return result

            # Check if we have numerical data for analysis
            if data and isinstance(data, (list, tuple)):
                # Try to convert to numerical data
                try:
                    numerical_data = [float(x) for x in data if str(x).replace('.', '').replace('-', '').isdigit()]
                    
                    if numerical_data and len(numerical_data) >= 2:
                        if "trend" in query_lower or "analyze" in query_lower:
                            analysis = self.analyze_trend(numerical_data)
                            
                            if "error" in analysis:
                                return analysis["error"]
                            
                            result = f"""**Trend Analysis:**
- Direction: {analysis['trend_direction']}
- Strength: {analysis['strength']} (correlation: {analysis['correlation']:.3f})
- Slope: {analysis['slope']:.3f}
- Data Points: {analysis['data_points']}
- Mean: {analysis['mean']:.2f}
- Standard Deviation: {analysis['std_dev']:.2f}

**Predictions for next 3 points:**
{', '.join([f'{pred:.2f}' for pred in analysis['predictions']])}"""
                            
                            return result
                            
                        elif "forecast" in query_lower or "predict" in query_lower:
                            forecast = self.simple_forecast(numerical_data)
                            
                            if "error" in forecast:
                                return forecast["error"]
                            
                            result = f"""**Forecast Results:**
Method: {forecast['method']}
Periods: {forecast['periods']}

**Forecasted Values:**
"""
                            for i, (pred, ci) in enumerate(zip(forecast['forecasts'], forecast['confidence_intervals'])):
                                result += f"Period {i+1}: {pred:.2f} (95% CI: {ci[0]:.2f} - {ci[1]:.2f})\n"
                            
                            return result
                
                except ValueError:
                    pass  # Data is not numerical
            
            # Search for relevant context in vector store
            search_results = vector_store.similarity_search(query, k=3)
            context = ""
            
            if search_results:
                context = "\n\n".join([result[0] for result in search_results])
            
            # General prediction query
            if "predict" in query_lower or "forecast" in query_lower or "future" in query_lower:
                return self.make_prediction(context, query)
            
            elif "analyze" in query_lower or "pattern" in query_lower or "trend" in query_lower:
                if context:
                    return self.analyze_pattern(context)
                else:
                    return "Please provide data or context for analysis."
            
            else:
                # General analytical approach
                prompt = f"""The user is asking: "{query}"

{f"Relevant context: {context}" if context else ""}

Please provide analytical insights, predictions, or data-driven responses based on the query. If specific data is needed but not provided, explain what type of data would be helpful."""
                
                response = model_manager.azure_llm.invoke(prompt)
                if hasattr(response, 'content'):
                    response = response.content
                return response
            
        except Exception as e:
            st.error(f"Failed to process prediction query: {e}")
            return "Sorry, I couldn't process your prediction request at the moment."

# Global prediction agent instance
prediction_agent = PredictionAgent()
