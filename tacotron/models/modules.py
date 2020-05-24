import tensorflow as tf


class HighwayNet:
	def __init__(self, units, name=None):
		self.units = units
		self.scope = 'HighwayNet' if name is None else name

		self.H_layer = tf.layers.Dense(units=self.units, activation=tf.nn.relu, name='H')
		self.T_layer = tf.layers.Dense(units=self.units, activation=tf.nn.sigmoid, name='T', bias_initializer=tf.constant_initializer(-1.))

	def __call__(self, inputs):
		with tf.variable_scope(self.scope):
			H = self.H_layer(inputs)
			T = self.T_layer(inputs)
			return H * T + inputs * (1. - T)


class CBHG:
	def __init__(self, K, conv_channels, pool_size, projections, projection_kernel_size, n_highwaynet_layers, highway_units, rnn_units, bnorm, is_training, name=None):
		self.K = K
		self.conv_channels = conv_channels
		self.pool_size = pool_size

		self.projections = projections
		self.projection_kernel_size = projection_kernel_size
		self.bnorm = bnorm

		self.is_training = is_training
		self.scope = 'CBHG' if name is None else name

		self.highway_units = highway_units
		self.highwaynet_layers = [HighwayNet(highway_units, name='{}_highwaynet_{}'.format(self.scope, i+1)) for i in range(n_highwaynet_layers)]
		self._fw_cell = tf.nn.rnn_cell.GRUCell(rnn_units, name='{}_forward_RNN'.format(self.scope))
		self._bw_cell = tf.nn.rnn_cell.GRUCell(rnn_units, name='{}_backward_RNN'.format(self.scope))

	def __call__(self, inputs, input_lengths):
		with tf.variable_scope(self.scope):
			with tf.variable_scope('conv_bank'):
				#Convolution bank: concatenate on the last axis to stack channels from all convolutions
				#The convolution bank uses multiple different kernel sizes to have many insights of the input sequence
				#This makes one of the strengths of the CBHG block on sequences.
				conv_outputs = tf.concat(
					[conv1d(inputs, k, self.conv_channels, tf.nn.relu, self.is_training, 0., self.bnorm, 'conv1d_{}'.format(k)) for k in range(1, self.K+1)],
					axis=-1
					)

			#Maxpooling (dimension reduction, Using max instead of average helps finding "Edges" in mels)
			maxpool_output = tf.layers.max_pooling1d(
				conv_outputs,
				pool_size=self.pool_size,
				strides=1,
				padding='same')

			#Two projection layers
			proj1_output = conv1d(maxpool_output, self.projection_kernel_size, self.projections[0], tf.nn.relu, self.is_training, 0., self.bnorm, 'proj1')
			proj2_output = conv1d(proj1_output, self.projection_kernel_size, self.projections[1], lambda _: _, self.is_training, 0., self.bnorm, 'proj2')

			#Residual connection
			highway_input = proj2_output + inputs

			#Additional projection in case of dimension mismatch (for HighwayNet "residual" connection)
			if highway_input.shape[2] != self.highway_units:
				highway_input = tf.layers.dense(highway_input, self.highway_units)

			#4-layer HighwayNet
			for highwaynet in self.highwaynet_layers:
				highway_input = highwaynet(highway_input)
			rnn_input = highway_input

			#Bidirectional RNN
			outputs, states = tf.nn.bidirectional_dynamic_rnn(
				self._fw_cell,
				self._bw_cell,
				rnn_input,
				sequence_length=input_lengths,
				dtype=tf.float32)
			return tf.concat(outputs, axis=2) #Concat forward and backward outputs


class ZoneoutLSTMCell(tf.nn.rnn_cell.RNNCell):
	'''Wrapper for tf LSTM to create Zoneout LSTM Cell

	inspired by:
	https://github.com/teganmaharaj/zoneout/blob/master/zoneout_tensorflow.py

	Published by one of 'https://arxiv.org/pdf/1606.01305.pdf' paper writers.

	Many thanks to @Ondal90 for pointing this out. You sir are a hero!
	'''
	def __init__(self, num_units, is_training, zoneout_factor_cell=0., zoneout_factor_output=0., state_is_tuple=True, name=None):
		'''Initializer with possibility to set different zoneout values for cell/hidden states.
		'''
		zm = min(zoneout_factor_output, zoneout_factor_cell)
		zs = max(zoneout_factor_output, zoneout_factor_cell)

		if zm < 0. or zs > 1.:
			raise ValueError('One/both provided Zoneout factors are not in [0, 1]')

		self._cell = tf.nn.rnn_cell.LSTMCell(num_units, state_is_tuple=state_is_tuple, name=name)
		self._zoneout_cell = zoneout_factor_cell
		self._zoneout_outputs = zoneout_factor_output
		self.is_training = is_training
		self.state_is_tuple = state_is_tuple

	@property
	def state_size(self):
		return self._cell.state_size

	@property
	def output_size(self):
		return self._cell.output_size

	def __call__(self, inputs, state, scope=None):
		'''Runs vanilla LSTM Cell and applies zoneout.
		'''
		#Apply vanilla LSTM
		output, new_state = self._cell(inputs, state, scope)

		if self.state_is_tuple:
			(prev_c, prev_h) = state
			(new_c, new_h) = new_state
		else:
			num_proj = self._cell._num_units if self._cell._num_proj is None else self._cell._num_proj
			prev_c = tf.slice(state, [0, 0], [-1, self._cell._num_units])
			prev_h = tf.slice(state, [0, self._cell._num_units], [-1, num_proj])
			new_c = tf.slice(new_state, [0, 0], [-1, self._cell._num_units])
			new_h = tf.slice(new_state, [0, self._cell._num_units], [-1, num_proj])

		#Apply zoneout
		if self.is_training:
			#nn.dropout takes keep_prob (probability to keep activations) not drop_prob (probability to mask activations)!
			c = (1 - self._zoneout_cell) * tf.nn.dropout(new_c - prev_c, (1 - self._zoneout_cell)) + prev_c
			h = (1 - self._zoneout_outputs) * tf.nn.dropout(new_h - prev_h, (1 - self._zoneout_outputs)) + prev_h

		else:
			c = (1 - self._zoneout_cell) * new_c + self._zoneout_cell * prev_c
			h = (1 - self._zoneout_outputs) * new_h + self._zoneout_outputs * prev_h

		new_state = tf.nn.rnn_cell.LSTMStateTuple(c, h) if self.state_is_tuple else tf.concat(1, [c, h])

		return output, new_state


class EncoderConvolutions:
	"""Encoder convolutional layers used to find local dependencies in inputs characters.
	"""
	def __init__(self, is_training, hparams, activation=tf.nn.relu, scope=None):
		"""
		Args:
			is_training: Boolean, determines if the model is training or in inference to control dropout
			kernel_size: tuple or integer, The size of convolution kernels
			channels: integer, number of convolutional kernels
			activation: callable, postnet activation function for each convolutional layer
			scope: Postnet scope.
		"""
		super(EncoderConvolutions, self).__init__()
		self.is_training = is_training

		self.kernel_size = hparams.enc_conv_kernel_size
		self.channels = hparams.enc_conv_channels
		self.activation = activation
		self.scope = 'enc_conv_layers' if scope is None else scope
		self.drop_rate = hparams.tacotron_dropout_rate
		self.enc_conv_num_layers = hparams.enc_conv_num_layers
		self.bnorm = hparams.batch_norm_position

	def __call__(self, inputs):
		with tf.variable_scope(self.scope):
			x = inputs
			for i in range(self.enc_conv_num_layers):
				x = conv1d(x, self.kernel_size, self.channels, self.activation,
					self.is_training, self.drop_rate, self.bnorm, 'conv_layer_{}_'.format(i + 1)+self.scope)
		return x


class EncoderRNN:
	"""Encoder bidirectional one layer LSTM
	"""
	def __init__(self, is_training, size=256, zoneout=0.1, scope=None):
		"""
		Args:
			is_training: Boolean, determines if the model is training or in inference to control zoneout
			size: integer, the number of LSTM units for each direction
			zoneout: the zoneout factor
			scope: EncoderRNN scope.
		"""
		super(EncoderRNN, self).__init__()
		self.is_training = is_training

		self.size = size
		self.zoneout = zoneout
		self.scope = 'encoder_LSTM' if scope is None else scope

		#Create forward LSTM Cell
		self._fw_cell = ZoneoutLSTMCell(size, is_training,
			zoneout_factor_cell=zoneout,
			zoneout_factor_output=zoneout,
			name='encoder_fw_LSTM')

		#Create backward LSTM Cell
		self._bw_cell = ZoneoutLSTMCell(size, is_training,
			zoneout_factor_cell=zoneout,
			zoneout_factor_output=zoneout,
			name='encoder_bw_LSTM')

	def __call__(self, inputs, input_lengths):
		with tf.variable_scope(self.scope):
			outputs, (fw_state, bw_state) = tf.nn.bidirectional_dynamic_rnn(
				self._fw_cell,
				self._bw_cell,
				inputs,
				sequence_length=input_lengths,
				dtype=tf.float32,
				swap_memory=True)

			return tf.concat(outputs, axis=2) # Concat and return forward + backward outputs


class Prenet:
	"""Two fully connected layers used as an information bottleneck for the attention.
	"""
	def __init__(self, is_training, layers_sizes=[256, 256], drop_rate=0.5, activation=tf.nn.relu, scope=None):
		"""
		Args:
			layers_sizes: list of integers, the length of the list represents the number of pre-net
				layers and the list values represent the layers number of units
			activation: callable, activation functions of the prenet layers.
			scope: Prenet scope.
		"""
		super(Prenet, self).__init__()
		self.drop_rate = drop_rate

		self.layers_sizes = layers_sizes
		self.activation = activation
		self.is_training = is_training

		self.scope = 'prenet' if scope is None else scope

	def __call__(self, inputs):
		x = inputs

		with tf.variable_scope(self.scope):
			for i, size in enumerate(self.layers_sizes):
				dense = tf.layers.dense(x, units=size, activation=self.activation,
					name='dense_{}'.format(i + 1))
				#The paper discussed introducing diversity in generation at inference time
				#by using a dropout of 0.5 only in prenet layers (in both training and inference).
				x = tf.layers.dropout(dense, rate=self.drop_rate, training=True,
					name='dropout_{}'.format(i + 1) + self.scope)
		return x


class DecoderRNN:
	"""Decoder two uni directional LSTM Cells
	"""
	def __init__(self, is_training, layers=2, size=1024, zoneout=0.1, scope=None):
		"""
		Args:
			is_training: Boolean, determines if the model is in training or inference to control zoneout
			layers: integer, the number of LSTM layers in the decoder
			size: integer, the number of LSTM units in each layer
			zoneout: the zoneout factor
		"""
		super(DecoderRNN, self).__init__()
		self.is_training = is_training

		self.layers = layers
		self.size = size
		self.zoneout = zoneout
		self.scope = 'decoder_rnn' if scope is None else scope

		#Create a set of LSTM layers
		self.rnn_layers = [ZoneoutLSTMCell(size, is_training,
			zoneout_factor_cell=zoneout,
			zoneout_factor_output=zoneout,
			name='decoder_LSTM_{}'.format(i+1)) for i in range(layers)]

		self._cell = tf.contrib.rnn.MultiRNNCell(self.rnn_layers, state_is_tuple=True)

	def __call__(self, inputs, states):
		with tf.variable_scope(self.scope):
			return self._cell(inputs, states)


class FrameProjection:
	"""Projection layer to r * num_mels dimensions or num_mels dimensions
	"""
	def __init__(self, shape=80, activation=None, scope=None):
		"""
		Args:
			shape: integer, dimensionality of output space (r*n_mels for decoder or n_mels for postnet)
			activation: callable, activation function
			scope: FrameProjection scope.
		"""
		super(FrameProjection, self).__init__()

		self.shape = shape
		self.activation = activation

		self.scope = 'Linear_projection' if scope is None else scope
		self.dense = tf.layers.Dense(units=shape, activation=activation, name='projection_{}'.format(self.scope))

	def __call__(self, inputs):
		with tf.variable_scope(self.scope):
			#If activation==None, this returns a simple Linear projection
			#else the projection will be passed through an activation function
			# output = tf.layers.dense(inputs, units=self.shape, activation=self.activation,
			# 	name='projection_{}'.format(self.scope))
			output = self.dense(inputs)

			return output


class StopProjection:
	"""Projection to a scalar and through a sigmoid activation
	"""
	def __init__(self, is_training, shape=1, activation=tf.nn.sigmoid, scope=None):
		"""
		Args:
			is_training: Boolean, to control the use of sigmoid function as it is useless to use it
				during training since it is integrate inside the sigmoid_crossentropy loss
			shape: integer, dimensionality of output space. Defaults to 1 (scalar)
			activation: callable, activation function. only used during inference
			scope: StopProjection scope.
		"""
		super(StopProjection, self).__init__()
		self.is_training = is_training

		self.shape = shape
		self.activation = activation
		self.scope = 'stop_token_projection' if scope is None else scope

	def __call__(self, inputs):
		with tf.variable_scope(self.scope):
			output = tf.layers.dense(inputs, units=self.shape,
				activation=None, name='projection_{}'.format(self.scope))

			#During training, don't use activation as it is integrated inside the sigmoid_cross_entropy loss function
			if self.is_training:
				return output
			return self.activation(output)


class Postnet:
	"""Postnet that takes final decoder output and fine tunes it (using vision on past and future frames)
	"""
	def __init__(self, is_training, hparams, activation=tf.nn.tanh, scope=None):
		"""
		Args:
			is_training: Boolean, determines if the model is training or in inference to control dropout
			kernel_size: tuple or integer, The size of convolution kernels
			channels: integer, number of convolutional kernels
			activation: callable, postnet activation function for each convolutional layer
			scope: Postnet scope.
		"""
		super(Postnet, self).__init__()
		self.is_training = is_training

		self.kernel_size = hparams.postnet_kernel_size
		self.channels = hparams.postnet_channels
		self.activation = activation
		self.scope = 'postnet_convolutions' if scope is None else scope
		self.postnet_num_layers = hparams.postnet_num_layers
		self.drop_rate = hparams.tacotron_dropout_rate
		self.bnorm = hparams.batch_norm_position

	def __call__(self, inputs):
		with tf.variable_scope(self.scope):
			x = inputs
			for i in range(self.postnet_num_layers - 1):
				x = conv1d(x, self.kernel_size, self.channels, self.activation,
					self.is_training, self.drop_rate, self.bnorm, 'conv_layer_{}_'.format(i + 1)+self.scope)
			x = conv1d(x, self.kernel_size, self.channels, lambda _: _, self.is_training, self.drop_rate, self.bnorm,
				'conv_layer_{}_'.format(5)+self.scope)
		return x


def conv1d(inputs, kernel_size, channels, activation, is_training, drop_rate, bnorm, scope):
	assert bnorm in ('before', 'after')
	with tf.variable_scope(scope):
		conv1d_output = tf.layers.conv1d(
			inputs,
			filters=channels,
			kernel_size=kernel_size,
			activation=activation if bnorm == 'after' else None,
			padding='same')
		batched = tf.layers.batch_normalization(conv1d_output, training=is_training)
		activated = activation(batched) if bnorm == 'before' else batched
		return tf.layers.dropout(activated, rate=drop_rate, training=is_training,
								name='dropout_{}'.format(scope))

def _round_up_tf(x, multiple):
	# Tf version of remainder = x % multiple
	remainder = tf.mod(x, multiple)
	# Tf version of return x if remainder == 0 else x + multiple - remainder
	x_round =  tf.cond(tf.equal(remainder, tf.zeros(tf.shape(remainder), dtype=tf.int32)),
		lambda: x,
		lambda: x + multiple - remainder)

	return x_round

def sequence_mask(lengths, r, expand=True):
	'''Returns a 2-D or 3-D tensorflow sequence mask depending on the argument 'expand'
	'''
	max_len = tf.reduce_max(lengths)
	max_len = _round_up_tf(max_len, tf.convert_to_tensor(r))
	if expand:
		return tf.expand_dims(tf.sequence_mask(lengths, maxlen=max_len, dtype=tf.float32), axis=-1)
	return tf.sequence_mask(lengths, maxlen=max_len, dtype=tf.float32)

def MaskedMSE(targets, outputs, targets_lengths, hparams, mask=None):
	'''Computes a masked Mean Squared Error
	'''

	#[batch_size, time_dimension, 1]
	#example:
	#sequence_mask([1, 3, 2], 5) = [[[1., 0., 0., 0., 0.]],
	#							    [[1., 1., 1., 0., 0.]],
	#							    [[1., 1., 0., 0., 0.]]]
	#Note the maxlen argument that ensures mask shape is compatible with r>1
	#This will by default mask the extra paddings caused by r>1
	if mask is None:
		mask = sequence_mask(targets_lengths, hparams.outputs_per_step, True)

	#[batch_size, time_dimension, channel_dimension(mels)]
	ones = tf.ones(shape=[tf.shape(mask)[0], tf.shape(mask)[1], tf.shape(targets)[-1]], dtype=tf.float32)
	mask_ = mask * ones

	with tf.control_dependencies([tf.assert_equal(tf.shape(targets), tf.shape(mask_))]):
		return tf.losses.mean_squared_error(labels=targets, predictions=outputs, weights=mask_)

def MaskedSigmoidCrossEntropy(targets, outputs, targets_lengths, hparams, mask=None):
	'''Computes a masked SigmoidCrossEntropy with logits
	'''

	#[batch_size, time_dimension]
	#example:
	#sequence_mask([1, 3, 2], 5) = [[1., 0., 0., 0., 0.],
	#							    [1., 1., 1., 0., 0.],
	#							    [1., 1., 0., 0., 0.]]
	#Note the maxlen argument that ensures mask shape is compatible with r>1
	#This will by default mask the extra paddings caused by r>1
	if mask is None:
		mask = sequence_mask(targets_lengths, hparams.outputs_per_step, False)

	with tf.control_dependencies([tf.assert_equal(tf.shape(targets), tf.shape(mask))]):
		#Use a weighted sigmoid cross entropy to measure the <stop_token> loss. Set hparams.cross_entropy_pos_weight to 1
		#will have the same effect as  vanilla tf.nn.sigmoid_cross_entropy_with_logits.
		losses = tf.nn.weighted_cross_entropy_with_logits(targets=targets, logits=outputs, pos_weight=hparams.cross_entropy_pos_weight)

	with tf.control_dependencies([tf.assert_equal(tf.shape(mask), tf.shape(losses))]):
		masked_loss = losses * mask

	return tf.reduce_sum(masked_loss) / tf.count_nonzero(masked_loss, dtype=tf.float32)

def MaskedLinearLoss(targets, outputs, targets_lengths, hparams, mask=None):
	'''Computes a masked MAE loss with priority to low frequencies
	'''

	#[batch_size, time_dimension, 1]
	#example:
	#sequence_mask([1, 3, 2], 5) = [[[1., 0., 0., 0., 0.]],
	#							    [[1., 1., 1., 0., 0.]],
	#							    [[1., 1., 0., 0., 0.]]]
	#Note the maxlen argument that ensures mask shape is compatible with r>1
	#This will by default mask the extra paddings caused by r>1
	if mask is None:
		mask = sequence_mask(targets_lengths, hparams.outputs_per_step, True)

	#[batch_size, time_dimension, channel_dimension(freq)]
	ones = tf.ones(shape=[tf.shape(mask)[0], tf.shape(mask)[1], tf.shape(targets)[-1]], dtype=tf.float32)
	mask_ = mask * ones

	l1 = tf.abs(targets - outputs)
	n_priority_freq = int(2000 / (hparams.sample_rate * 0.5) * hparams.num_freq)

	with tf.control_dependencies([tf.assert_equal(tf.shape(targets), tf.shape(mask_))]):
		masked_l1 = l1 * mask_
		masked_l1_low = masked_l1[:,:,0:n_priority_freq]

	mean_l1 = tf.reduce_sum(masked_l1) / tf.reduce_sum(mask_)
	mean_l1_low = tf.reduce_sum(masked_l1_low) / tf.reduce_sum(mask_)

	return 0.5 * mean_l1 + 0.5 * mean_l1_low

def softmax_focal_loss(labels, logits, alpha=None, gamma=0):
	'''
	@param label (tf.int32): [batch_size] (NOT one-hot!)
	@param logits (tf.float32): [batch_size, num_of_cls]
	@param alpha : [num_of_cls]
	@return : focal_loss = - alphat
	'''
	labels = tf.cast(labels, tf.int32)

	if alpha is not None:
		alpha = tf.constant(alpha, dtype=tf.float32)
		a_t = tf.gather(alpha, labels, axis=0) # -> [batch_size, 1]
	
	labels = tf.reshape(labels, [-1, 1])
	logits = tf.gather(logits, labels, axis=1) # -> [batch_size, 1]
	p_t = tf.reshape(tf.nn.softmax(logits), [-1]) # -> [batch_size]
	log_p_t = -tf.log(p_t) # - log(p_t)
	
	if alpha is not None:
		log_p_t = a_t * log_p_t	# - a_t * log(p_t)

	return tf.reduce_mean(tf.pow((1-pt), float(gamma)) * log_p_t) # - a_t * (1 - p_t)^gamma * log(p_t)


def shape_list(x):
    """Return list of dims, statically where possible."""
    x = tf.convert_to_tensor(x)

    # If unknown rank, return dynamic shape
    if x.get_shape().dims is None:
        return tf.shape(x)

    static = x.get_shape().as_list()
    shape = tf.shape(x)

    ret = []
    for i in range(len(static)):
        dim = static[i]
        if dim is None:
            dim = shape[i]
        ret.append(dim)
    return ret


class ReferenceEncoder:
    def __init__(self, hparams, is_training=True, activation=tf.nn.relu, layer_sizes=(32, 32, 64, 64, 128, 128)):
        self._layer_sizes = layer_sizes
        self._n_layers = len(layer_sizes)
        self._hparams = hparams
        self._is_training = is_training
        self._activation = activation

    def __call__(self, inputs):
        # CNN stacks
        # inputs: [batch_size,n_frame,frame_size]
        x = tf.expand_dims(inputs, axis=-1)
        for i in range(self._n_layers):
            with tf.variable_scope('reference_encoder_{}'.format(i)):
                x = tf.layers.conv2d(x, filters=self._layer_sizes[i], kernel_size=3, strides=(2, 2), padding='same',
                                     activation=tf.nn.relu)
                x = tf.layers.batch_normalization(x, training=self._is_training)
                if self._activation is not None:
                    x = self._activation(x)
        # x: [batch_size,seq_len,embed_size,channels]
        shapes = shape_list(x)
        # x: [batch_size,seq_len,embed_size*channels], preserving the output time resolution
        x = tf.reshape(x, shapes[:-2] + [shapes[2] * shapes[3]])
        return x



def multihead_attention(queries,
                        keys,
                        num_units=None,
                        num_heads=8,
						input_alignment=None,
                        dropout_rate=0.,
                        is_training=True,
                        causality=False,
                        scope='multihead_attention',
                        reuse=None):
    '''Applies multihead attention.

    Args:
      queries: A 3d tensor with shape of [N, T_q, C_q].
      keys: A 3d tensor with shape of [N, T_k, C_k].
      num_units: A scalar. Attention size: output dim
      dropout_rate: A floating point number.
      is_training: Boolean. Controller of mechanism for dropout.
      causality: Boolean. If true, units that reference the future are masked.
      num_heads: An int. Number of heads.
      scope: Optional scope for `variable_scope`.
      reuse: Boolean, whether to reuse the weights of a previous layer
        by the same name.

    Returns
      A 3d tensor with shape of (N, T_q, C)
    '''
    with tf.variable_scope(scope, reuse=reuse):
        # Set the fall back option for num_units
        if num_units is None:
            num_units = queries.get_shape().as_list[-1]

        # Linear projections
        Q = tf.layers.dense(queries, num_units, use_bias=False)  # (N, T_q, C)
        K = tf.layers.dense(keys, num_units, use_bias=False)  # (N, T_k, C)
        V = tf.layers.dense(keys, num_units, use_bias=False)  # (N, T_k, C)

        # Split and concat
        Q_ = tf.concat(tf.split(Q, num_heads, axis=2), axis=0)  # (h*N, T_q, C/h)
        K_ = tf.concat(tf.split(K, num_heads, axis=2), axis=0)  # (h*N, T_k, C/h)
        V_ = tf.concat(tf.split(V, num_heads, axis=2), axis=0)  # (h*N, T_k, C/h)

        # Multiplication
        outputs = tf.matmul(Q_, tf.transpose(K_, [0, 2, 1]))  # (h*N, T_q, T_k)

        # Scale
        outputs = outputs / (K_.get_shape().as_list()[-1] ** 0.5)

        # Key Masking
        key_masks = tf.sign(tf.abs(tf.reduce_sum(keys, axis=-1)))  # (N, T_k)
        key_masks = tf.tile(key_masks, [num_heads, 1])  # (h*N, T_k)
        key_masks = tf.tile(tf.expand_dims(key_masks, 1), [1, tf.shape(queries)[1], 1])  # (h*N, T_q, T_k)

        paddings = tf.ones_like(outputs) * (-2 ** 32 + 1)
        outputs = tf.where(tf.equal(key_masks, 0), paddings, outputs)  # (h*N, T_q, T_k)

        # Causality = Future blinding
        if causality:
            diag_vals = tf.ones_like(outputs[0, :, :])  # (T_q, T_k)
            tril = tf.contrib.linalg.LinearOperatorLowerTriangular(diag_vals).to_dense()  # (T_q, T_k)
            masks = tf.tile(tf.expand_dims(tril, 0), [tf.shape(outputs)[0], 1, 1])  # (h*N, T_q, T_k)

            paddings = tf.ones_like(masks) * (-2 ** 32 + 1)
            outputs = tf.where(tf.equal(masks, 0), paddings, outputs)  # (h*N, T_q, T_k)
            
        logits = outputs
        # Restore shape
        logits = tf.concat(tf.split(logits, num_heads, axis=0), axis=2)  # [N,T_q,C]

        # Activation
        outputs = tf.nn.softmax(outputs)  # (h*N, T_q, T_k)

        alignment = outputs
        # Restore shape
        alignment = tf.concat(tf.split(alignment, num_heads, axis=0), axis=2)  # [N,T_q,C]


        # Query Masking
        query_masks = tf.sign(tf.abs(tf.reduce_sum(queries, axis=-1)))  # (N, T_q)
        query_masks = tf.tile(query_masks, [num_heads, 1])  # (h*N, T_q)
        query_masks = tf.tile(tf.expand_dims(query_masks, -1), [1, 1, tf.shape(keys)[1]])  # (h*N, T_q, T_k)
        outputs *= query_masks  # broadcasting. (N, T_q, C)

        if input_alignment is not None:
            alignment = input_alignment
            outputs = input_alignment
        
        # Dropouts
        outputs = tf.layers.dropout(outputs, rate=dropout_rate, training=tf.convert_to_tensor(is_training))

        # Weighted sum
        outputs = tf.matmul(outputs, V_)  # (h*N, T_q, C/h)

        # Restore shape
        outputs = tf.concat(tf.split(outputs, num_heads, axis=0), axis=2)  # (N, T_q, C)

        # ADD & NORM
        # Residual connection
        # extra op ?
        # outputs += Q  # ?

        # Normalize
        # outputs = normalize(outputs)  # (N, T_q, C)

    return outputs, logits, alignment


class StyleTokenLayer:
    def __init__(self, output_size, is_training=True, scope=None, num_heads=4):
        self._output_size = output_size
        self._is_training = is_training
        self._scope = 'style_token' if scope is None else scope
        self._num_heads = num_heads

    def __call__(self, inputs, token_embedding, input_alignment=None):
        # inputs: [batch_size,1,hp.tacotron_reference_gru_hidden_size], query
        # output: [batch_size,1,attention_output_size]
        x = inputs
        with tf.variable_scope(self._scope):
            token_embedding = tf.nn.tanh(token_embedding)  # tanh activation before attention
            # print('x: {}'.format(x))
            # print('token_embedding: {}'.format(token_embedding))
            x, logits, alignment = multihead_attention(queries=x, keys=token_embedding, num_units=self._output_size, dropout_rate=0.5,
                                       is_training=self._is_training, num_heads=self._num_heads, input_alignment=input_alignment)
            return x, logits, alignment