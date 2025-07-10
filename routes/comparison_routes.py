from flask import Blueprint, request, jsonify, render_template, current_app, session
from services.comparison import Comparison
from app import db
from models import Dataset, Analysis
import logging

comparison_bp = Blueprint('comparison', __name__, url_prefix='/api/comparison')

@comparison_bp.route('/datasets', methods=['GET'])
def get_datasets():
    """Get all available datasets for analysis operations"""
    try:
        # Query all datasets from the database
        datasets = Dataset.query.all()
        dataset_list = []

        # Iterate through each dataset and format the data for JSON response
        for dataset in datasets:
            dataset_list.append({
                'id': dataset.id,
                'filename': dataset.filename,
                'rows': dataset.num_rows,
                'columns': dataset.num_columns,
                'file_size': dataset.file_size,
                # Safely format the upload timestamp:
                # If dataset.created_at is None, assign None. Otherwise, call isoformat().
                'created_at': dataset.upload_timestamp.isoformat() if dataset.upload_timestamp else None
            })

        # Return a successful JSON response with the list of datasets
        return jsonify({
            'success': True,
            'datasets': dataset_list
        })

    except Exception as e:
        # Log the error on the server side for debugging
        logging.error(f"Error fetching datasets: {str(e)}")
        # Return a JSON response indicating failure and the error message, with a 500 status code
        return jsonify({'success': False, 'error': f"An internal server error occurred while retrieving datasets: {str(e)}"}), 500

@comparison_bp.route('/columns/<int:dataset_id>', methods=['POST'])
def compare_columns(dataset_id):
    try:
        data = request.get_json()
        columns = data.get('columns', [])
        comparison_type = data.get('comparison_type', 'statistical')
        
        comparer = Comparison()
        result = comparer.compare_columns(dataset_id, columns, comparison_type)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Column comparison error: {str(e)}")
        return jsonify({'error': f'Column comparison failed: {str(e)}'}), 500

@comparison_bp.route('/numerical/<int:dataset_id>')
def compare_numerical(dataset_id):
    try:
        column1 = request.args.get('column1')
        column2 = request.args.get('column2')
        comparer = Comparison()
        result = comparer.compare_numerical(dataset_id, column1, column2)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Numerical comparison error: {str(e)}")
        return jsonify({'error': f'Numerical comparison failed: {str(e)}'}), 500

@comparison_bp.route('/categorical/<int:dataset_id>')
def compare_categorical(dataset_id):
    try:
        column1 = request.args.get('column1')
        column2 = request.args.get('column2')
        comparer = Comparison()
        result = comparer.compare_categorical(dataset_id, column1, column2)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Categorical comparison error: {str(e)}")
        return jsonify({'error': f'Categorical comparison failed: {str(e)}'}), 500

@comparison_bp.route('/mixed/<int:dataset_id>')
def compare_mixed(dataset_id):
    try:
        numerical_column = request.args.get('numerical_column')
        categorical_column = request.args.get('categorical_column')
        comparer = Comparison()
        result = comparer.compare_mixed(dataset_id, numerical_column, categorical_column)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Mixed comparison error: {str(e)}")
        return jsonify({'error': f'Mixed comparison failed: {str(e)}'}), 500

@comparison_bp.route('/groups/<int:dataset_id>')
def compare_groups(dataset_id):
    try:
        target_column = request.args.get('target_column')
        group_column = request.args.get('group_column')
        comparer = Comparison()
        result = comparer.compare_groups(dataset_id, target_column, group_column)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Group comparison error: {str(e)}")
        return jsonify({'error': f'Group comparison failed: {str(e)}'}), 500

@comparison_bp.route('/distributions/<int:dataset_id>')
def compare_distributions(dataset_id):
    try:
        columns = request.args.getlist('columns')
        comparer = Comparison()
        result = comparer.compare_distributions(dataset_id, columns)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Distribution comparison error: {str(e)}")
        return jsonify({'error': f'Distribution comparison failed: {str(e)}'}), 500

@comparison_bp.route('/correlations/<int:dataset_id>')
def compare_correlations(dataset_id):
    try:
        target_column = request.args.get('target_column')
        comparer = Comparison()
        result = comparer.compare_correlations(dataset_id, target_column)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Correlation comparison error: {str(e)}")
        return jsonify({'error': f'Correlation comparison failed: {str(e)}'}), 500

@comparison_bp.route('/importance/<int:dataset_id>')
def compare_importance(dataset_id):
    try:
        target_column = request.args.get('target_column')
        method = request.args.get('method', 'mutual_info')
        comparer = Comparison()
        result = comparer.compare_importance(dataset_id, target_column, method)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Importance comparison error: {str(e)}")
        return jsonify({'error': f'Importance comparison failed: {str(e)}'}), 500

@comparison_bp.route('/temporal/<int:dataset_id>')
def compare_temporal(dataset_id):
    try:
        columns = request.args.getlist('columns')
        date_column = request.args.get('date_column')
        comparer = Comparison()
        result = comparer.compare_temporal(dataset_id, columns, date_column)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Temporal comparison error: {str(e)}")
        return jsonify({'error': f'Temporal comparison failed: {str(e)}'}), 500

@comparison_bp.route('/segments/<int:dataset_id>')
def compare_segments(dataset_id):
    try:
        target_column = request.args.get('target_column')
        segment_column = request.args.get('segment_column')
        comparer = Comparison()
        result = comparer.compare_segments(dataset_id, target_column, segment_column)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Segment comparison error: {str(e)}")
        return jsonify({'error': f'Segment comparison failed: {str(e)}'}), 500

@comparison_bp.route('/outliers/<int:dataset_id>')
def compare_outliers(dataset_id):
    try:
        columns = request.args.getlist('columns')
        method = request.args.get('method', 'iqr')
        comparer = Comparison()
        result = comparer.compare_outliers(dataset_id, columns, method)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Outlier comparison error: {str(e)}")
        return jsonify({'error': f'Outlier comparison failed: {str(e)}'}), 500

@comparison_bp.route('/summary/<int:dataset_id>')
def comparison_summary(dataset_id):
    try:
        columns = request.args.getlist('columns')
        comparer = Comparison()
        result = comparer.comparison_summary(dataset_id, columns)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Comparison summary error: {str(e)}")
        return jsonify({'error': f'Comparison summary failed: {str(e)}'}), 500

@comparison_bp.route('/recommendations/<int:dataset_id>')
def comparison_recommendations(dataset_id):
    try:
        columns = request.args.getlist('columns')
        comparer = Comparison()
        result = comparer.get_comparison_recommendations(dataset_id, columns)
        return jsonify(result)
    except Exception as e:
        current_app.logger.error(f"Comparison recommendations error: {str(e)}")
        return jsonify({'error': f'Comparison recommendations failed: {str(e)}'}), 500