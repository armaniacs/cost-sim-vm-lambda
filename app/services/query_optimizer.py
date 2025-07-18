"""
Query Optimization Service for Database Performance Enhancement.

This service provides:
- Query analysis and optimization
- Index recommendations
- Query plan analysis
- Performance profiling
- Automated query tuning
"""

import logging
import re
import time
from typing import Any, Dict, List, Optional, Tuple

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session

from app.extensions import db
from app.models.database import Base

logger = logging.getLogger(__name__)


class QueryAnalyzer:
    """Analyzes SQL queries for performance optimization."""
    
    def __init__(self):
        self.query_patterns = {
            'select_star': r'SELECT\s+\*\s+FROM',
            'no_where': r'SELECT\s+.*\s+FROM\s+\w+(?!\s+WHERE)',
            'no_limit': r'SELECT\s+.*\s+FROM\s+\w+(?!\s+LIMIT)',
            'cartesian_join': r'FROM\s+\w+\s*,\s*\w+',
            'subquery_in_select': r'SELECT\s+.*\(\s*SELECT\s+.*\)\s+FROM',
            'or_in_where': r'WHERE\s+.*\s+OR\s+',
            'function_in_where': r'WHERE\s+.*\w+\s*\(',
            'like_prefix': r'LIKE\s+\'%\w+',
        }
        
        self.optimization_rules = {
            'select_star': {
                'severity': 'medium',
                'message': 'Avoid SELECT * - specify column names explicitly',
                'suggestion': 'Replace SELECT * with specific column names'
            },
            'no_where': {
                'severity': 'high',
                'message': 'Query without WHERE clause may scan entire table',
                'suggestion': 'Add WHERE clause to limit rows'
            },
            'no_limit': {
                'severity': 'medium',
                'message': 'Query without LIMIT may return too many rows',
                'suggestion': 'Add LIMIT clause to prevent large result sets'
            },
            'cartesian_join': {
                'severity': 'high',
                'message': 'Cartesian join detected - may cause performance issues',
                'suggestion': 'Add JOIN conditions to avoid cartesian product'
            },
            'subquery_in_select': {
                'severity': 'medium',
                'message': 'Subquery in SELECT may cause N+1 query problem',
                'suggestion': 'Consider using JOINs instead of subqueries'
            },
            'or_in_where': {
                'severity': 'medium',
                'message': 'OR conditions may prevent index usage',
                'suggestion': 'Consider using UNION or separate queries'
            },
            'function_in_where': {
                'severity': 'medium',
                'message': 'Functions in WHERE clause may prevent index usage',
                'suggestion': 'Avoid functions on indexed columns in WHERE'
            },
            'like_prefix': {
                'severity': 'high',
                'message': 'LIKE with leading wildcard cannot use indexes',
                'suggestion': 'Avoid leading wildcards in LIKE patterns'
            }
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """Analyze query and return optimization suggestions."""
        issues = []
        
        # Normalize query for analysis
        normalized_query = query.upper().strip()
        
        # Check for performance issues
        for pattern_name, pattern in self.query_patterns.items():
            if re.search(pattern, normalized_query, re.IGNORECASE):
                rule = self.optimization_rules.get(pattern_name)
                if rule:
                    issues.append({
                        'type': pattern_name,
                        'severity': rule['severity'],
                        'message': rule['message'],
                        'suggestion': rule['suggestion']
                    })
        
        # Calculate complexity score
        complexity_score = self._calculate_complexity(normalized_query)
        
        return {
            'query': query,
            'issues': issues,
            'complexity_score': complexity_score,
            'estimated_performance': self._estimate_performance(complexity_score, issues)
        }
    
    def _calculate_complexity(self, query: str) -> int:
        """Calculate query complexity score."""
        score = 0
        
        # Count joins
        joins = len(re.findall(r'\bJOIN\b', query))
        score += joins * 2
        
        # Count subqueries
        subqueries = len(re.findall(r'\bSELECT\b', query)) - 1
        score += subqueries * 3
        
        # Count aggregations
        aggregations = len(re.findall(r'\b(COUNT|SUM|AVG|MIN|MAX)\b', query))
        score += aggregations * 1
        
        # Count ORDER BY
        order_by = len(re.findall(r'\bORDER BY\b', query))
        score += order_by * 1
        
        # Count GROUP BY
        group_by = len(re.findall(r'\bGROUP BY\b', query))
        score += group_by * 2
        
        return score
    
    def _estimate_performance(self, complexity_score: int, issues: List[Dict]) -> str:
        """Estimate query performance based on complexity and issues."""
        high_severity_issues = len([i for i in issues if i['severity'] == 'high'])
        
        if high_severity_issues > 0 or complexity_score > 10:
            return 'poor'
        elif complexity_score > 5:
            return 'moderate'
        else:
            return 'good'


class IndexRecommender:
    """Recommends database indexes for query optimization."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def analyze_table_queries(self, table_name: str, queries: List[str]) -> List[Dict[str, Any]]:
        """Analyze queries for a specific table and recommend indexes."""
        recommendations = []
        
        for query in queries:
            # Extract WHERE conditions
            where_columns = self._extract_where_columns(query, table_name)
            
            # Extract ORDER BY columns
            order_by_columns = self._extract_order_by_columns(query, table_name)
            
            # Extract JOIN columns
            join_columns = self._extract_join_columns(query, table_name)
            
            # Generate index recommendations
            if where_columns:
                recommendations.append({
                    'type': 'where_index',
                    'table': table_name,
                    'columns': where_columns,
                    'priority': 'high',
                    'reason': 'Improve WHERE clause performance'
                })
            
            if order_by_columns:
                recommendations.append({
                    'type': 'order_index',
                    'table': table_name,
                    'columns': order_by_columns,
                    'priority': 'medium',
                    'reason': 'Improve ORDER BY performance'
                })
            
            if join_columns:
                recommendations.append({
                    'type': 'join_index',
                    'table': table_name,
                    'columns': join_columns,
                    'priority': 'high',
                    'reason': 'Improve JOIN performance'
                })
        
        return self._deduplicate_recommendations(recommendations)
    
    def _extract_where_columns(self, query: str, table_name: str) -> List[str]:
        """Extract columns used in WHERE clause."""
        # Simple regex to find WHERE conditions
        where_pattern = r'WHERE\s+.*?(?=\s+(?:ORDER|GROUP|HAVING|LIMIT|$))'
        where_match = re.search(where_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not where_match:
            return []
        
        where_clause = where_match.group(0)
        
        # Extract column names (simplified)
        column_pattern = r'\b(\w+)\s*[=<>!]'
        columns = re.findall(column_pattern, where_clause)
        
        return list(set(columns))
    
    def _extract_order_by_columns(self, query: str, table_name: str) -> List[str]:
        """Extract columns used in ORDER BY clause."""
        order_pattern = r'ORDER\s+BY\s+(.*?)(?=\s+(?:LIMIT|$))'
        order_match = re.search(order_pattern, query, re.IGNORECASE | re.DOTALL)
        
        if not order_match:
            return []
        
        order_clause = order_match.group(1)
        
        # Extract column names
        columns = []
        for column in order_clause.split(','):
            column = column.strip().split()[0]  # Remove ASC/DESC
            columns.append(column)
        
        return columns
    
    def _extract_join_columns(self, query: str, table_name: str) -> List[str]:
        """Extract columns used in JOIN conditions."""
        join_pattern = r'JOIN\s+\w+\s+ON\s+(.*?)(?=\s+(?:WHERE|ORDER|GROUP|HAVING|LIMIT|JOIN|$))'
        join_matches = re.findall(join_pattern, query, re.IGNORECASE | re.DOTALL)
        
        columns = []
        for join_condition in join_matches:
            # Extract column names from join condition
            column_pattern = r'\b(\w+)\s*='
            join_columns = re.findall(column_pattern, join_condition)
            columns.extend(join_columns)
        
        return list(set(columns))
    
    def _deduplicate_recommendations(self, recommendations: List[Dict]) -> List[Dict]:
        """Remove duplicate index recommendations."""
        unique_recommendations = []
        seen = set()
        
        for rec in recommendations:
            key = (rec['table'], tuple(sorted(rec['columns'])))
            if key not in seen:
                seen.add(key)
                unique_recommendations.append(rec)
        
        return unique_recommendations
    
    def get_existing_indexes(self, table_name: str) -> List[Dict[str, Any]]:
        """Get existing indexes for a table."""
        try:
            with self.engine.connect() as conn:
                # PostgreSQL specific query
                query = text("""
                    SELECT
                        indexname,
                        indexdef,
                        tablename
                    FROM pg_indexes
                    WHERE tablename = :table_name
                """)
                
                result = conn.execute(query, {'table_name': table_name})
                
                indexes = []
                for row in result:
                    indexes.append({
                        'name': row.indexname,
                        'definition': row.indexdef,
                        'table': row.tablename
                    })
                
                return indexes
                
        except Exception as e:
            logger.error(f"Error getting existing indexes: {e}")
            return []
    
    def generate_index_ddl(self, recommendation: Dict[str, Any]) -> str:
        """Generate DDL statement for index creation."""
        table = recommendation['table']
        columns = recommendation['columns']
        index_type = recommendation['type']
        
        # Generate index name
        index_name = f"idx_{table}_{index_type}_{'_'.join(columns)}"
        
        # Generate CREATE INDEX statement
        columns_str = ', '.join(columns)
        ddl = f"CREATE INDEX {index_name} ON {table} ({columns_str});"
        
        return ddl


class QueryProfiler:
    """Profiles query execution for performance analysis."""
    
    def __init__(self, engine: Engine):
        self.engine = engine
    
    def profile_query(self, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Profile query execution and return performance metrics."""
        start_time = time.time()
        
        try:
            with self.engine.connect() as conn:
                # Execute EXPLAIN ANALYZE for PostgreSQL
                explain_query = f"EXPLAIN ANALYZE {query}"
                
                explain_result = conn.execute(text(explain_query), params or {})
                explain_output = [row[0] for row in explain_result]
                
                # Execute actual query
                query_start = time.time()
                result = conn.execute(text(query), params or {})
                rows = result.fetchall()
                query_time = time.time() - query_start
                
                # Parse EXPLAIN output
                explain_analysis = self._parse_explain_output(explain_output)
                
                return {
                    'query': query,
                    'execution_time': query_time,
                    'row_count': len(rows),
                    'explain_analysis': explain_analysis,
                    'explain_output': explain_output,
                    'total_time': time.time() - start_time
                }
                
        except Exception as e:
            logger.error(f"Query profiling error: {e}")
            return {
                'query': query,
                'error': str(e),
                'execution_time': time.time() - start_time
            }
    
    def _parse_explain_output(self, explain_output: List[str]) -> Dict[str, Any]:
        """Parse EXPLAIN ANALYZE output to extract key metrics."""
        analysis = {
            'total_cost': 0,
            'actual_time': 0,
            'rows': 0,
            'loops': 0,
            'planning_time': 0,
            'execution_time': 0,
            'index_usage': [],
            'sequential_scans': []
        }
        
        for line in explain_output:
            if 'cost=' in line:
                # Extract cost information
                cost_match = re.search(r'cost=(\d+\.\d+)\.\.(\d+\.\d+)', line)
                if cost_match:
                    analysis['total_cost'] = float(cost_match.group(2))
            
            if 'actual time=' in line:
                # Extract actual time
                time_match = re.search(r'actual time=(\d+\.\d+)\.\.(\d+\.\d+)', line)
                if time_match:
                    analysis['actual_time'] = float(time_match.group(2))
            
            if 'rows=' in line:
                # Extract row count
                rows_match = re.search(r'rows=(\d+)', line)
                if rows_match:
                    analysis['rows'] = int(rows_match.group(1))
            
            if 'Planning Time:' in line:
                # Extract planning time
                planning_match = re.search(r'Planning Time: (\d+\.\d+)', line)
                if planning_match:
                    analysis['planning_time'] = float(planning_match.group(1))
            
            if 'Execution Time:' in line:
                # Extract execution time
                execution_match = re.search(r'Execution Time: (\d+\.\d+)', line)
                if execution_match:
                    analysis['execution_time'] = float(execution_match.group(1))
            
            if 'Index Scan' in line:
                analysis['index_usage'].append(line.strip())
            
            if 'Seq Scan' in line:
                analysis['sequential_scans'].append(line.strip())
        
        return analysis


class QueryOptimizer:
    """Main query optimization service."""
    
    def __init__(self, engine: Engine = None):
        self.engine = engine or db.engine
        self.analyzer = QueryAnalyzer()
        self.index_recommender = IndexRecommender(self.engine)
        self.profiler = QueryProfiler(self.engine)
    
    def optimize_query(self, query: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Comprehensive query optimization analysis."""
        # Analyze query for issues
        analysis = self.analyzer.analyze_query(query)
        
        # Profile query execution
        profiling = self.profiler.profile_query(query, params)
        
        # Generate optimized query suggestions
        optimized_query = self._generate_optimized_query(query, analysis['issues'])
        
        return {
            'original_query': query,
            'analysis': analysis,
            'profiling': profiling,
            'optimized_query': optimized_query,
            'performance_improvement': self._calculate_improvement(analysis, profiling)
        }
    
    def _generate_optimized_query(self, query: str, issues: List[Dict]) -> str:
        """Generate optimized version of the query."""
        optimized = query
        
        for issue in issues:
            if issue['type'] == 'select_star':
                # Replace SELECT * with specific columns based on common table patterns
                if 'users' in optimized.lower():
                    optimized = optimized.replace('SELECT *', 'SELECT id, email, created_at, is_active')
                elif 'calculations' in optimized.lower():
                    optimized = optimized.replace('SELECT *', 'SELECT id, configuration, result, created_at')
                elif 'pricing' in optimized.lower():
                    optimized = optimized.replace('SELECT *', 'SELECT id, provider, region, service, price, timestamp')
                else:
                    optimized = f"-- Optimized: Replace SELECT * with specific columns\n{optimized}"
            
            elif issue['type'] == 'no_limit':
                if 'LIMIT' not in optimized.upper():
                    optimized = f"{optimized.rstrip(';')} LIMIT 1000;"
            
            elif issue['type'] == 'no_where':
                # Add common WHERE clauses based on table patterns
                if 'users' in optimized.lower():
                    optimized = optimized.replace('FROM users', 'FROM users WHERE is_active = true')
                elif 'calculations' in optimized.lower():
                    optimized = optimized.replace('FROM calculations', 'FROM calculations WHERE created_at >= NOW() - INTERVAL \'30 days\'')
                elif 'pricing' in optimized.lower():
                    optimized = optimized.replace('FROM pricing', 'FROM pricing WHERE timestamp >= NOW() - INTERVAL \'7 days\'')
                else:
                    optimized = f"-- Optimized: Add WHERE clause to limit results\n{optimized}"
        
        return optimized
    
    def _calculate_improvement(self, analysis: Dict, profiling: Dict) -> str:
        """Calculate potential performance improvement."""
        high_issues = len([i for i in analysis['issues'] if i['severity'] == 'high'])
        
        if high_issues > 2:
            return 'high'
        elif high_issues > 0 or analysis['complexity_score'] > 5:
            return 'medium'
        else:
            return 'low'
    
    def get_table_optimization_report(self, table_name: str) -> Dict[str, Any]:
        """Generate comprehensive optimization report for a table."""
        # Get existing indexes
        existing_indexes = self.index_recommender.get_existing_indexes(table_name)
        
        # Get table statistics
        table_stats = self._get_table_statistics(table_name)
        
        # Generate sample queries for analysis
        sample_queries = self._generate_sample_queries(table_name)
        
        # Analyze queries and generate recommendations
        recommendations = self.index_recommender.analyze_table_queries(table_name, sample_queries)
        
        return {
            'table_name': table_name,
            'existing_indexes': existing_indexes,
            'table_statistics': table_stats,
            'index_recommendations': recommendations,
            'sample_queries': sample_queries
        }
    
    def _get_table_statistics(self, table_name: str) -> Dict[str, Any]:
        """Get table statistics for optimization analysis."""
        try:
            with self.engine.connect() as conn:
                # Get table size and row count
                stats_query = text("""
                    SELECT
                        schemaname,
                        tablename,
                        attname,
                        n_distinct,
                        correlation
                    FROM pg_stats
                    WHERE tablename = :table_name
                """)
                
                result = conn.execute(stats_query, {'table_name': table_name})
                
                stats = []
                for row in result:
                    stats.append({
                        'schema': row.schemaname,
                        'table': row.tablename,
                        'column': row.attname,
                        'distinct_values': row.n_distinct,
                        'correlation': row.correlation
                    })
                
                return {
                    'column_statistics': stats,
                    'analysis_timestamp': time.time()
                }
                
        except Exception as e:
            logger.error(f"Error getting table statistics: {e}")
            return {}
    
    def _generate_sample_queries(self, table_name: str) -> List[str]:
        """Generate sample queries for analysis."""
        # This would typically be based on actual query logs
        # For now, return common query patterns
        return [
            f"SELECT * FROM {table_name} WHERE id = 1",
            f"SELECT * FROM {table_name} ORDER BY created_at DESC LIMIT 10",
            f"SELECT COUNT(*) FROM {table_name} WHERE status = 'active'",
            f"SELECT * FROM {table_name} WHERE created_at > NOW() - INTERVAL '1 day'"
        ]


# Global query optimizer instance
query_optimizer = QueryOptimizer()