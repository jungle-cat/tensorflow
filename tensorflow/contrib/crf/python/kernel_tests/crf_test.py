# Copyright 2016 The TensorFlow Authors. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ==============================================================================
"""Tests for CRF."""

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import itertools

import numpy as np

from tensorflow.contrib.crf.python.ops import crf
from tensorflow.python.framework import constant_op
from tensorflow.python.ops import array_ops
from tensorflow.python.ops import math_ops
from tensorflow.python.platform import test


class CrfTest(test.TestCase):

  def testCrfSequenceScore(self):
    inputs = np.array(
        [[4, 5, -3], [3, -1, 3], [-1, 2, 1], [0, 0, 0]], dtype=np.float32)
    tag_indices = np.array([1, 2, 1, 0], dtype=np.int32)
    transition_params = np.array(
        [[0, 0, 0, 0], [-3, 5, -2, 0], [3, 4, 1, 0], [1, 2, 1, 0]], dtype=np.float32)
    sequence_lengths = np.array(3, dtype=np.int32)
    with self.test_session() as sess:
      sequence_score = crf.crf_sequence_score(
          inputs=array_ops.expand_dims(inputs, 0),
          targets=array_ops.expand_dims(tag_indices, 0),
          sequence_lengths=array_ops.expand_dims(sequence_lengths, 0),
          transition_params=constant_op.constant(transition_params))
      sequence_score = array_ops.squeeze(sequence_score, [0])
      tf_sequence_score = sess.run(sequence_score)
      expected_unary_score = sum(inputs[i][tag_indices[i]]
                                 for i in range(sequence_lengths))
      expected_binary_score = sum(
          transition_params[1:, :-1][tag_indices[i], tag_indices[i + 1]]
          for i in range(sequence_lengths - 1))
      expected_sequence_score = expected_unary_score + expected_binary_score
      self.assertAllClose(tf_sequence_score, expected_sequence_score)

  def testCrfUnaryScore(self):
    inputs = np.array(
        [[4, 5, -3], [3, -1, 3], [-1, 2, 1], [0, 0, 0]], dtype=np.float32)
    tag_indices = np.array([1, 2, 1, 0], dtype=np.int32)
    sequence_lengths = np.array(3, dtype=np.int32)
    with self.test_session() as sess:
      unary_score = crf.crf_unary_score(
          targets=array_ops.expand_dims(tag_indices, 0),
          sequence_lengths=array_ops.expand_dims(sequence_lengths, 0),
          inputs=array_ops.expand_dims(inputs, 0))
      unary_score = array_ops.squeeze(unary_score, [0])
      tf_unary_score = sess.run(unary_score)
      expected_unary_score = sum(inputs[i][tag_indices[i]]
                                 for i in range(sequence_lengths))
      self.assertAllClose(tf_unary_score, expected_unary_score)

  def testCrfBinaryScore(self):
    tag_indices = np.array([1, 2, 1, 0], dtype=np.int32)
    transition_params = np.array(
        [[0, 0, 0, 0], [-3, 5, -2, 0], [3, 4, 1, 0], [1, 2, 1, 0]], dtype=np.float32)
    sequence_lengths = np.array(3, dtype=np.int32)
    with self.test_session() as sess:
      binary_score = crf.crf_binary_score(
          targets=array_ops.expand_dims(tag_indices, 0),
          sequence_lengths=array_ops.expand_dims(sequence_lengths, 0),
          transition_params=constant_op.constant(transition_params))
      binary_score = array_ops.squeeze(binary_score, [0])
      tf_binary_score = sess.run(binary_score)
      expected_binary_score = sum(
          transition_params[1:, :-1][tag_indices[i], tag_indices[i + 1]]
          for i in range(sequence_lengths - 1))
      self.assertAllClose(tf_binary_score, expected_binary_score)

  def testCrfLogNorm(self):
    inputs = np.array(
        [[4, 5, -3], [3, -1, 3], [-1, 2, 1], [0, 0, 0]], dtype=np.float32)
    transition_params = np.array(
        [[0, 0, 0, 0], [-3, 5, -2, 0], [3, 4, 1, 0], [1, 2, 1, 0]], dtype=np.float32)
    num_words = inputs.shape[0]
    num_tags = inputs.shape[1]
    sequence_lengths = np.array(3, dtype=np.int32)
    with self.test_session() as sess:
      all_sequence_scores = []

      # Compare the dynamic program with brute force computation.
      for tag_indices in itertools.product(
          range(num_tags), repeat=sequence_lengths):
        tag_indices = list(tag_indices)
        tag_indices.extend([0] * (num_words - sequence_lengths))
        all_sequence_scores.append(
            crf.crf_sequence_score(
                inputs=array_ops.expand_dims(inputs, 0),
                targets=array_ops.expand_dims(tag_indices, 0),
                sequence_lengths=array_ops.expand_dims(sequence_lengths, 0),
                transition_params=constant_op.constant(transition_params)))

      brute_force_log_norm = math_ops.reduce_logsumexp(all_sequence_scores)
      log_norm = crf.crf_log_norm(
          inputs=array_ops.expand_dims(inputs, 0),
          sequence_lengths=array_ops.expand_dims(sequence_lengths, 0),
          transition_params=constant_op.constant(transition_params))
      log_norm = array_ops.squeeze(log_norm, [0])
      tf_brute_force_log_norm, tf_log_norm = sess.run(
          [brute_force_log_norm, log_norm])

      self.assertAllClose(tf_log_norm, tf_brute_force_log_norm)

if __name__ == "__main__":
  test.main()
